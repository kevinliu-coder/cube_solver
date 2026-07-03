"""Cube visualizer — LSLL method (IDA* cross + thistle3 phases)."""
import json, os, pickle
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from twophase import solve, verify
from tables import load, MOVE_NAMES
from cubie import CubieCube, MOVES
import coord as C

HERE = os.path.dirname(os.path.abspath(__file__))
load()
T = load()

# Cross heuristic (from existing cross table)
CROSS_E = [4,5,6,7]
F2L_C = [4,5,6,7]; F2L_E = [8,9,10,11]
U_C = [0,1,2,3]; U_E = [0,1,2,3]

CROSS_CACHE = os.path.join(HERE, "cross_table.pkl")
with open(CROSS_CACHE, "rb") as f:
    _cross_dist = pickle.load(f)["dist"]

def cross_heuristic(cube):
    st = (tuple(cube.ep[i] for i in CROSS_E), tuple(cube.eo[i] for i in CROSS_E))
    return _cross_dist.get(st, 99)

def _opp(f): return (f + 3) % 6
def _allowed(f, l1, l2):
    if l1 == -1: return True
    if f == l1: return False
    return not (l2 != -1 and f == l2 and _opp(f) == l1)

def ida_cross(cube):
    sol = []
    def search(c, depth, bound, last1, last2):
        h = cross_heuristic(c)
        if h == 0: return True
        if depth + h > bound: return False
        for mv in MOVE_NAMES:
            face = ord(mv[0]) - ord('U')
            if not _allowed(face, last1, last2): continue
            nc = c.copy(); nc.multiply(MOVES[mv])
            sol.append(mv)
            if search(nc, depth+1, bound, face, last1): return True
            sol.pop()
        return False
    for bound in range(cross_heuristic(cube), 9):
        sol.clear()
        if search(cube, 0, bound, -1, -1): return sol[:]
    return None

def solve4_full(scramble):
    from thistle3 import _extra, G0_IDX, G1_IDX, G2_IDX, _ida_stage
    E = _extra()
    
    cube = CubieCube()
    if scramble:
        for m in scramble.split():
            if m in MOVES: cube.multiply(MOVES[m])
    
    phases = []
    
    # Phase 1: Cross (IDA* with heuristic)
    cross = ida_cross(cube)
    if cross:
        for m in cross: cube.multiply(MOVES[m])
        phases.append({"name":"十字 Cross", "desc":f"底面棱归位 ({len(cross)}步, 直觉)", "moves":cross})
    
    # Phase 2: EO (≈双F2L)
    flip = C.get_flip(cube)
    if flip != 0:
        s1 = _ida_stage((flip,), [T["flip_move"]], (0,), G0_IDX, 18, lambda c: E["prun_flip"][c[0]])
        if s1:
            ms = [MOVE_NAMES[m] for m in s1]
            for m in ms: cube.multiply(MOVES[m])
            phases.append({"name":"双 F2L", "desc":f"棱定向+双pair ({len(ms)}步, ~200公式)", "moves":ms})
    
    # Phase 3: LSLL (twist+slice)
    tw, sl = C.get_twist(cube), C.get_slice(cube)
    if (tw, sl) != (0, C.SLICE_SOLVED):
        s2 = _ida_stage((tw, sl), [E["tw14"], E["sl14"]], (0, C.SLICE_SOLVED), G1_IDX, 14,
                        lambda c: E["prun_tw_sl_g1"][c[0]*C.N_SLICE + c[1]])
        if s2:
            ms = [MOVE_NAMES[m] for m in s2]
            for m in ms: cube.multiply(MOVES[m])
            phases.append({"name":"LSLL", "desc":f"最后一对+顶层色向 ({len(ms)}步, ~1700公式)", "moves":ms})
    
    # Phase 4: PLL
    cp = C.get_corner_perm(cube); ep = C.get_edge8_perm(cube); sp = C.get_slice_perm(cube)
    if (cp, ep, sp) != (0, 0, 0):
        s3 = _ida_stage((cp, ep, sp), [T["cperm_move"], T["eperm_move"], T["sperm_move"]], (0, 0, 0), G2_IDX, 10,
                        lambda c: max(T["prun_cperm_sperm"][c[0]*C.N_SPERM + c[2]], T["prun_eperm_sperm"][c[1]*C.N_SPERM + c[2]]))
        if s3:
            ms = [MOVE_NAMES[m] for m in s3]
            for m in ms: cube.multiply(MOVES[m])
            phases.append({"name":"PLL", "desc":f"顶层位置 ({len(ms)}步)", "moves":ms})
    
    total = sum(len(p["moves"]) for p in phases)
    return {"phases": phases, "total": total, "ok": cube.is_solved()}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=HERE, **k)
    def log_message(self, *a): pass
    def _json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/solve":
            scr = parse_qs(parsed.query).get("scramble", [""])[0].strip()
            try: sol, n = solve(scr, timeout=5.0); ok = bool(sol and (n==0 or verify(scr, sol)))
            except: sol, n, ok = None, -1, False
            self._json({"solution": sol or "", "n": n, "ok": ok})
            return
        if parsed.path == "/solve4":
            scr = parse_qs(parsed.query).get("scramble", [""])[0].strip()
            self._json(solve4_full(scr))
            return
        if parsed.path == "/lsll":
            # Legacy LSLL demo — use a simple case
            from cubie import CubieCube as CC, MOVES as MV
            c = CC()
            for m in "R U R' U' R' F R F'".split(): c.multiply(MV[m])
            tw, sl = C.get_twist(c), C.get_slice(c)
            from thistle3 import _extra, G1_IDX, G2_IDX, _ida_stage
            E = _extra()
            s2 = _ida_stage((tw, sl), [E["tw14"], E["sl14"]], (0, C.SLICE_SOLVED), G1_IDX, 14,
                            lambda c: E["prun_tw_sl_g1"][c[0]*C.N_SLICE + c[1]])
            lsll = [MOVE_NAMES[m] for m in s2]
            for m in lsll: c.multiply(MV[MOVE_NAMES[m]])
            cp, ep, sp = C.get_corner_perm(c), C.get_edge8_perm(c), C.get_slice_perm(c)
            s3 = _ida_stage((cp, ep, sp), [T["cperm_move"], T["eperm_move"], T["sperm_move"]], (0, 0, 0), G2_IDX, 10,
                            lambda c: max(T["prun_cperm_sperm"][c[0]*C.N_SPERM + c[2]], T["prun_eperm_sperm"][c[1]*C.N_SPERM + c[2]]))
            pll = [MOVE_NAMES[m] for m in s3] if s3 else []
            self._json({"setup": "R U R' U' R' F R F'", "lsll": lsll, "lsll_n": len(lsll), "pll": pll, "pll_n": len(pll)})
            return
        return super().do_GET()

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
