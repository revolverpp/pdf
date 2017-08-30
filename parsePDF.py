import re
import zlib
import sys

if len(sys.argv) > 1:
	path = sys.argv[1]
else:
	print sys.argv[0] + " <file.pdf>"
	exit(-1)

f = open(path, "rb").read()
streams = []
fonts = []
cmaps = []

for s in re.findall("stream.*?endstream", f, re.DOTALL):
	inflated = {"content" : zlib.decompress(s[7 : len(s) - 10])}
	inflated["position"] = f.index(s)
	streams.append(inflated)

for x in range(len(streams)):
	found = False
	if "beginbfchar" in streams[x]["content"]:
		k = streams[x]["position"]
		for j in range(k, 0, -1):
			if f[j : j+3] == "obj":
				for y in range(j, j-10, -1):
					if f[y] == chr(0x0a):
						resid = f[y+1 : j-1]
						cmap = {}
						cmap["id"] = resid
						cmap["content"] = streams[x]["content"]
						cmaps.append(cmap)
						found = True
						break
			if found:
				break

for fnt in re.findall("obj\n<<\n/BaseFont.*?>>", f, re.DOTALL):
	touni = re.findall("/ToUnicode.*?R", fnt)
	if len(touni) < 1:
		continue
	touni = touni[0]
	pos = f.index(fnt)
	for j in range(pos, 0, -1):
		if f[j] == chr(0x0a):
			font = {}
			font["id"] = f[j+1 : pos-3]
			font["unicode"] = touni[11 : len(touni) - 2]
			fonts.append(font)
			break

def toUnicode(cmap, text):
	d = re.findall("beginbfchar.*?endbfchar", cmap["content"], re.DOTALL)[0]
	chars = d.split("\n")
	del chars[0]
	del chars[len(chars) - 1]
	table = {}
	for c in chars:
		p = re.findall("<.*?> ", c)
		c1 = p[0][1 : len(p[0]) - 2]
		c2 = p[1][1 : len(p[1]) - 2]
		c1 = int(c1, base=16)
		c2 = int(c2, base=16)
		table[c1] = c2
	chars = re.findall("\\\\[0-9][0-9][0-9]", text)
	for c in chars:
		x = int(c[2:], base=8)
		try:
			print chr(table[x]),
		except KeyError:
			pass
		except ValueError:
			pass

def findFont(spec):
	spec = spec[2:]
	for font in fonts:
		if spec == font["id"]:
			return font

def findCmap(addr):
	for cmap in cmaps:
		if addr == cmap["id"]:
			return cmap

s10 = streams[10]["content"]
texts = re.findall("BT.*?ET", s10, re.DOTALL)
for text in texts:
	font = re.findall("/F[0-9]{1,}", text)[0]
	font = findFont(font)
	cmap = findCmap(font["unicode"])
	toUnicode(cmap, text)
