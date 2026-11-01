import hashlib
import os
import struct
import sys

exe, ext, src = sys.argv[1], sys.argv[2], sys.argv[3]

d = open(exe, "rb").read()
e = struct.unpack_from("<I", d, 0x3C)[0]
opt = e + 24
nsec = struct.unpack_from("<H", d, e + 6)[0]
sizeopt = struct.unpack_from("<H", d, e + 20)[0]
magic = struct.unpack_from("<H", d, opt)[0]
subsystem = struct.unpack_from("<H", d, opt + 68)[0]
imagebase = struct.unpack_from("<I", d, opt + 28)[0]

print("=== CABECERA PE ===")
print("DOS magic      :", d[:2])
print("PE sig         :", d[e:e + 4], "en offset", hex(e))
print("Machine        : 0x%04x  (0x014c = Intel i386 / PE32)" % struct.unpack_from("<H", d, e + 4)[0])
print("Secciones      :", nsec)
print("Optional magic : 0x%04x  (0x010b = PE32, 0x020b = PE32+)" % magic)
print("Subsystem      : %d  (2 = Windows GUI)" % subsystem)
print("ImageBase      : 0x%x" % imagebase)
print("Firma NSIS     :", b"NullsoftInst" in d)

i = d.find(b"\xbd\x04\xef\xfe")
ms, ls = struct.unpack_from("<II", d, i + 8)
pv, rv = struct.unpack_from("<II", d, i + 16)
print("\n=== VERSION (VS_FIXEDFILEINFO) ===")
print("FileVersion    : %d.%d.%d.%d" % (ms >> 16, ms & 0xffff, ls >> 16, ls & 0xffff))
print("ProductVersion : %d.%d.%d.%d" % (pv >> 16, pv & 0xffff, rv >> 16, rv & 0xffff))

print("\n=== CADENAS UTF-16 ===")
for s in ("PitMasterAudio 5.19.1", "PitMasterAudio", "5.19.1", "PitmasterAI"):
    print("  %-26s %s" % (s, s.encode("utf-16-le") in d))

def walk(root, skip):
    out = {}
    for dp, dns, fns in os.walk(root):
        if os.path.relpath(dp, root) == ".":
            dns[:] = [x for x in dns if x not in skip]
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.normpath(os.path.relpath(p, root))
            if rel.split(os.sep)[0] in skip:
                continue
            out[rel] = p
    return out

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

S = walk(src, set())
E = walk(ext, {"$PLUGINSDIR"})
print("\n=== PAYLOAD vs ARBOL ORIGEN ===")
print("ficheros origen :", len(S))
print("ficheros payload:", len(E))
print("faltan          :", sorted(set(S) - set(E))[:5], "(%d)" % len(set(S) - set(E)))
print("sobran          :", sorted(set(E) - set(S)))
bad = [r for r in S if r in E and (os.path.getsize(S[r]) != os.path.getsize(E[r]) or md5(S[r]) != md5(E[r]))]
print("distintos       :", bad[:5], "(%d)" % len(bad))

print("\n=== MARCADORES DENTRO DEL PAYLOAD ===")
a = os.path.join(ext, "app", "analiza.py")
print("app/analiza.py existe      :", os.path.exists(a), os.path.getsize(a) if os.path.exists(a) else "")
app_py = open(os.path.join(ext, "app", "app.py"), encoding="utf-8", errors="replace").read()
print("_pico_real en app/app.py   :", "def _pico_real" in app_py)
app_js = open(os.path.join(ext, "app", "static", "app.js"), encoding="utf-8", errors="replace").read()
print("icono-preset en app.js     :", app_js.count("icono-preset"), "ocurrencias")
print("python/python.exe          :", os.path.getsize(os.path.join(ext, "python", "python.exe")), "bytes")
print("PitMasterAudio.vbs         :", os.path.getsize(os.path.join(ext, "PitMasterAudio.vbs")), "bytes")
