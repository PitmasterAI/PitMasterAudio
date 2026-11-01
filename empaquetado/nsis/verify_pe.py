import struct

exe = "/home/iaradio/pitmasteraudio-dist/PitMasterAudio-5.19.0-Setup.exe"
d = open(exe, "rb").read()

print("--- cadenas UTF-16 (metadata de version) ---")
for s in ("PitMasterAudio", "5.19.0", "5.19.0.0", "PitmasterAI",
          "Instalador de PitMasterAudio", "Masterizador de audio local",
          "pitmasterai.es"):
    print("  %-32s %s" % (s, s.encode("utf-16-le") in d))

e = struct.unpack_from("<I", d, 0x3C)[0]
opt = e + 24
nsec = struct.unpack_from("<H", d, e + 6)[0]
sizeopt = struct.unpack_from("<H", d, e + 20)[0]
magic = struct.unpack_from("<H", d, opt)[0]
dd = opt + (96 if magic == 0x10b else 112)
rva_res, sz_res = struct.unpack_from("<II", d, dd + 2 * 8)

secs = []
for i in range(nsec):
    o = e + 24 + sizeopt + i * 40
    name = d[o:o + 8].rstrip(b"\0").decode("latin-1")
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", d, o + 8)
    secs.append((name, vaddr, max(vsize, rawsize), rawptr))


def off(rva):
    for name, vaddr, size, rawptr in secs:
        if vaddr <= rva < vaddr + size:
            return rawptr + (rva - vaddr)
    raise ValueError(hex(rva))


print("\n--- recursos PE ---")
base = off(rva_res)
nname, nid = struct.unpack_from("<HH", d, base + 12)
TYPES = {3: "RT_ICON", 14: "RT_GROUP_ICON", 16: "RT_VERSION", 24: "RT_MANIFEST"}
HIGH = 0x80000000
for i in range(nname + nid):
    o = base + 16 + i * 8
    nm, offv = struct.unpack_from("<II", d, o)
    if nm >= HIGH:
        sp = base + (nm - HIGH)
        ln = struct.unpack_from("<H", d, sp)[0]
        label = d[sp + 2:sp + 2 + ln * 2].decode("utf-16-le")
    else:
        label = TYPES.get(nm, "tipo %d" % nm)
    if offv >= HIGH:
        sub = base + (offv - HIGH)
        ns, ni = struct.unpack_from("<HH", d, sub + 12)
        total = ns + ni
        # identificar el primer hijo (nombre o ID)
        first = "?"
        if total:
            cnm, coff = struct.unpack_from("<II", d, sub + 16)
            first = ("str" if cnm >= HIGH else str(cnm))
        print("  %-16s entradas nivel 2: %-3d (primera: %s)" % (label, total, first))

print("\nSecciones:", [s[0] for s in secs])
print("Tamano tabla recursos:", sz_res, "bytes")
tag = d.rfind(b"NullsoftInst")
print("Firma 'NullsoftInst' en:", hex(tag), "de", hex(len(d)))
