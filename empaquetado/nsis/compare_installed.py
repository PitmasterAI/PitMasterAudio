import hashlib
import os
import sys

inst, src = sys.argv[1], sys.argv[2]
IGNORE = {"pitmasteraudio.ico", "Desinstalar.exe", "datos"}

def walk(root):
    out = {}
    for dp, dns, fns in os.walk(root):
        rel_dir = os.path.relpath(dp, root)
        if rel_dir == ".":
            dns[:] = [d for d in dns if d not in IGNORE]
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.normpath(os.path.relpath(p, root))
            if rel in IGNORE or rel.split(os.sep)[0] in IGNORE:
                continue
            out[rel] = p
    return out

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

S, I = walk(src), walk(inst)
print("arbol origen   :", len(S))
print("instalado      :", len(I))
miss = sorted(set(S) - set(I))
extra = sorted(set(I) - set(S))
print("faltan         :", len(miss), miss[:4])
print("sobran         :", len(extra), extra[:4])
bad = [r for r in S if r in I and (os.path.getsize(S[r]) != os.path.getsize(I[r]) or md5(S[r]) != md5(I[r]))]
print("distintos      :", len(bad), bad[:4])
print("RESULTADO      :", "IDENTICO" if not miss and not bad else "DIFERENCIAS")
