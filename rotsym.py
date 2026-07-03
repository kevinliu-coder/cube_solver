"""Whole-cube rotation symmetries y (90° about U axis) and z2 (180° flip
about the F axis), as CubieCube relabelings, used to fold the one-look
table by viewing angle.

Conjugation convention (right-action model from cubie.py):
    conj(s, g) = g^-1 * s * g
which relabels state s into the rotated frame. Verified below by the move
relations  conj(MOVE[X], g) == MOVE[sigma_g(X)].
"""
from cubie import CubieCube, MOVES

def _inv(c: CubieCube) -> CubieCube:
    r = CubieCube()
    for i in range(8):
        r.cp[c.cp[i]] = i
    for i in range(8):
        r.co[i] = (-c.co[c.cp.index(i)]) % 3
    for i in range(12):
        r.ep[c.ep[i]] = i
    for i in range(12):
        r.eo[i] = (-c.eo[c.ep.index(i)]) % 2
    return r

def _mul(a: CubieCube, b: CubieCube) -> CubieCube:
    r = a.copy()
    r.multiply(b)
    return r

def conj(s: CubieCube, g: CubieCube) -> CubieCube:
    return _mul(_mul(_inv(g), s), g)

# ---- y: rotate whole cube like U (F->L, L->B, B->R, R->F) ----
# corners: top layer cycles like U, bottom like D'; no twist (U/D stickers stay U/D)
# edges: top like U, bottom like D'; slice edges cycle FR<-BR, FL<-FR, BL<-FL, BR<-BL
# slice-edge orientation picks up a flip (F/B-primary sticker moves to L/R face).
Y_ROT = CubieCube(
    cp=[3, 0, 1, 2, 7, 4, 5, 6], co=[0] * 8,
    ep=[3, 0, 1, 2, 7, 4, 5, 6, 11, 8, 9, 10],
    eo=[0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
)

# ---- z2: flip the cube upside down about the F axis (U<->D, R<->L) ----
Z2_ROT = CubieCube(
    cp=[5, 4, 7, 6, 1, 0, 3, 2], co=[0] * 8,
    ep=[6, 5, 4, 7, 2, 1, 0, 3, 9, 8, 11, 10],
    eo=[0] * 12,
)

# face relabeling under conjugation: conj(MOVE[X], g) == MOVE[FACE_MAP[g][X]]
Y_FACE = {"U": "U", "D": "D", "R": "F", "F": "L", "L": "B", "B": "R"}
Z2_FACE = {"U": "D", "D": "U", "R": "L", "L": "R", "F": "F", "B": "B"}

def map_move(mv: str, face_map: dict) -> str:
    return face_map[mv[0]] + mv[1:]

def map_alg(alg: list, face_map: dict) -> list:
    return [map_move(m, face_map) for m in alg]

# the 8 viewing angles: (rotation cube, face map applied that many times)
def _compose_maps(m1, m2):
    return {f: m2[m1[f]] for f in m1}

def build_syms():
    """Return list of (sym_cube, face_map) for the 8 viewing angles <y, z2>."""
    syms = []
    g = CubieCube()
    fmap = {f: f for f in "URFDLB"}
    for _ in range(4):
        syms.append((g.copy(), dict(fmap)))
        syms.append((_mul(g, Z2_ROT), _compose_maps(fmap, Z2_FACE)))
        g = _mul(g, Y_ROT)
        fmap = _compose_maps(fmap, Y_FACE)
    return syms

if __name__ == "__main__":
    def expect(name, cond):
        print(f"[{'OK ' if cond else 'FAIL'}] {name}")
        assert cond, name

    # y^4 = id, z2^2 = id
    y4 = CubieCube()
    for _ in range(4):
        y4 = _mul(y4, Y_ROT)
    expect("y^4 = I", y4.is_solved())
    expect("z2^2 = I", _mul(Z2_ROT, Z2_ROT).is_solved())

    # conjugation relabels moves exactly per the face maps
    for name, rot, fmap in [("y", Y_ROT, Y_FACE), ("z2", Z2_ROT, Z2_FACE)]:
        for f in "URFDLB":
            for suf in ["", "2", "'"]:
                got = conj(MOVES[f + suf], rot)
                want = MOVES[map_move(f + suf, fmap)]
                assert got == want, (name, f + suf)
        print(f"[OK ] conj by {name} maps all 18 moves correctly")

    # 8 distinct viewing angles
    syms = build_syms()
    keys = {tuple(s.cp + s.ep + s.eo) for s, _ in syms}
    expect("8 distinct symmetries", len(keys) == 8)
    print("\nall rotation-symmetry self tests passed.")
