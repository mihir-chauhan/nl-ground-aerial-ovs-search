"""Toy ground-aerial open-vocabulary search world.

World generator, simulated open-vocabulary detector, message channels
(templated natural language with a rule-based parser, fixed-schema symbolic
tuples) and the scripted frontier agents. Everything is deterministic given
(seed, tier, episode index); perception noise is drawn once per world so that
all systems are compared on common random numbers.
"""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

N = 30
GROUPS = [
    ["mug", "bottle", "glass", "bowl"],
    ["laptop", "phone", "tablet", "remote"],
    ["backpack", "box", "basket", "bucket"],
    ["hammer", "wrench", "drill", "scissors"],
    ["ball", "teddy", "book", "shoe"],
]
CLASSES = [c for g in GROUPS for c in g]
SYNONYMS = ["cup", "flask", "tumbler", "dish", "notebook", "handset", "slate", "clicker",
            "rucksack", "carton", "hamper", "pail", "mallet", "spanner", "borer", "shears",
            "sphere", "plushie", "novel", "sneaker"]
COLORS = ["red", "blue", "green", "yellow", "black", "white"]
LANDMARKS = ["sofa", "table", "bed", "shelf", "desk"]
ROOMS = ["kitchen", "lounge", "office", "bedroom", "workshop", "storage", "hall", "lab"]
TIERS = ["exact", "synonym", "attribute", "relational"]
NC, NCOL, NLM = len(CLASSES), len(COLORS), len(LANDMARKS)

DEFAULTS = dict(
    cap=100,            # step cap per episode
    n_fill=9,           # filler objects (plus target and two distractors)
    p_roof=0.3,         # probability that a room is covered (hidden from the aerial robot)
    r_ground=3,         # ground sensing radius (Chebyshev, same room only)
    r_air=4,            # aerial footprint radius (Chebyshev)
    air_speed=2,        # aerial cells per step
    res=3,              # aerial position quantisation block (cells)
    p_conf=0.2,         # aerial label confusion probability (within similarity group)
    p_col=0.7,          # probability the aerial robot perceives the colour
    sig_g=0.05,         # ground detector score noise
    sig_a=0.10,         # aerial detector score noise
    noise=1.0,          # multiplier on sig_g, sig_a and p_conf
    tau_g=0.75,         # ground candidate threshold
    tau_send=0.6,       # aerial report threshold on the class-slot score
    tau_r=0.7,          # receiver threshold on a re-scored message entry
    inspect_g=3,        # steps for a ground close-range inspection
    inspect_a=10,       # steps for an aerial descend-and-verify
    K=5,                # a robot may send one message every K steps
    M=2,                # sighting entries per message
    corrupt=0.0,        # message corruption rate
    intent_pen=15.0,    # frontier cost penalty for the teammate's announced room
    dist_scale=50.0,    # remote-candidate utility = score - distance / dist_scale
    prio=0,             # 1: only the second robot yields to the teammate's announced room
    team="GA",          # GA ground+aerial, GG two ground, AA two aerial, G single ground
)

# ---------------------------------------------------------------- embeddings
_D = 64


def _unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _build_embeddings():
    r = np.random.default_rng(12345)
    g = _unit(r.standard_normal((len(GROUPS), _D)))
    cls = _unit(0.6 * np.repeat(g, 4, axis=0) + 0.8 * _unit(r.standard_normal((NC, _D))))
    syn = _unit(cls + 0.55 * _unit(r.standard_normal((NC, _D))))
    csh = _unit(r.standard_normal(_D))
    col = _unit(0.5 * csh + 0.87 * _unit(r.standard_normal((NCOL, _D))))
    lsh = _unit(r.standard_normal(_D))
    lm = _unit(0.5 * lsh + 0.87 * _unit(r.standard_normal((NLM, _D))))
    clip = lambda a: np.clip(a, 0.0, 1.0)
    return dict(cls_cls=clip(cls @ cls.T), syn_cls=clip(syn @ cls.T),
                col=clip(col @ col.T), lm=clip(lm @ lm.T))


EMB = _build_embeddings()


class Query:
    """A text query: class word (canonical or synonym), optional colour, optional landmark."""

    def __init__(self, tier, cls, color, lm):
        self.tier, self.cls = tier, cls
        self.color = color if tier == "attribute" else None
        self.lm = lm if tier == "relational" else None
        self.cls_sim = EMB["syn_cls"][cls] if tier == "synonym" else EMB["cls_cls"][cls]

    def text(self):
        w = SYNONYMS[self.cls] if self.tier == "synonym" else CLASSES[self.cls]
        if self.color is not None:
            return "the %s %s" % (COLORS[self.color], w)
        if self.lm is not None:
            return "the %s near the %s" % (w, LANDMARKS[self.lm])
        return "the %s" % w

    def class_score(self, label):
        return float(self.cls_sim[label])

    def score(self, label, color, lm):
        """Slot-wise similarity. color: -1 unknown. lm: -1 none, -2 unknown."""
        s = [self.cls_sim[label]]
        if self.color is not None:
            s.append(0.5 if color < 0 else EMB["col"][self.color, color])
        if self.lm is not None:
            s.append(0.5 if lm == -2 else (0.0 if lm == -1 else EMB["lm"][self.lm, lm]))
        return float(np.mean(s))


# ---------------------------------------------------------------- world
class World:
    def __init__(self, rng, tier, P):
        self.P = P
        for _ in range(200):
            if self._generate(rng, tier):
                return
        raise RuntimeError("world generation failed")

    def _layout(self, rng):
        n_rooms = int(rng.integers(4, 9))
        rects, doors = [(0, 0, N, N)], []
        wall = np.zeros((N, N), bool)
        dead = set()
        while len(rects) < n_rooms:
            cands = [r for r in rects if r not in dead and max(r[2] - r[0], r[3] - r[1]) >= 13]
            if not cands:
                break
            r = max(cands, key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
            x0, y0, x1, y1 = r
            vert = (x1 - x0) >= (y1 - y0)   # wall is a line of constant x
            lo, hi = (x0, x1) if vert else (y0, y1)
            a0, a1 = (y0, y1) if vert else (x0, x1)
            opts = []
            for c in range(lo + 6, hi - 6):
                bad = False
                for (dx, dy) in doors:
                    da, dc = (dy, dx) if vert else (dx, dy)   # along-wall coord, across coord
                    # this wall's line is c; it ends next to walls at a0-1 and a1
                    if dc == c and da in (a0 - 1, a1):
                        bad = True
                if not bad:
                    opts.append(c)
            if not opts:
                dead.add(r)
                continue
            c = int(rng.choice(opts))
            d1 = int(rng.integers(a0, a1))
            ds = [d1]
            if a1 - a0 >= 12:
                far = [d for d in range(a0, a1) if abs(d - d1) >= 4]
                ds.append(int(rng.choice(far)))
            for a in range(a0, a1):
                if a not in ds:
                    wall[(c, a) if vert else (a, c)] = True
            for d in ds:
                doors.append((c, d) if vert else (d, c))
            rects.remove(r)
            if vert:
                rects += [(x0, y0, c, y1), (c + 1, y0, x1, y1)]
            else:
                rects += [(x0, y0, x1, c), (x0, c + 1, x1, y1)]
        return rects, doors, wall

    def _generate(self, rng, tier):
        P = self.P
        rects, doors, wall = self._layout(rng)
        if len(rects) < 4:
            return False
        nr = len(rects)
        room = -np.ones((N, N), int)
        for i, (x0, y0, x1, y1) in enumerate(rects):
            room[x0:x1, y0:y1] = i
        for (dx, dy) in doors:
            room[dx, dy] = -1
        free = ~wall
        # all-pairs ground distances
        idx = np.arange(N * N).reshape(N, N)
        rows, cols = [], []
        for sx, sy in ((1, 0), (0, 1)):
            a = idx[: N - sx, : N - sy][free[: N - sx, : N - sy] & free[sx:, sy:]]
            b = idx[sx:, sy:][free[: N - sx, : N - sy] & free[sx:, sy:]]
            rows += [a, b]
            cols += [b, a]
        rows, cols = np.concatenate(rows), np.concatenate(cols)
        G = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(N * N, N * N))
        D = shortest_path(G, method="D", unweighted=True)
        f = idx[free]
        if not np.isfinite(D[f[0], f]).all():
            return False
        self.rects, self.wall, self.room, self.free, self.D, self.nr = rects, wall, room, free, D, nr
        self.room_names = [ROOMS[i] for i in rng.permutation(len(ROOMS))[:nr]]
        roofed = rng.random(nr) < P["p_roof"]
        if roofed.all():
            roofed[int(rng.integers(nr))] = False
        self.roofed = roofed
        self.roof = np.zeros((N, N), bool)
        self.roof[room >= 0] = roofed[room[room >= 0]]
        self.room_cells = room >= 0

        used = set()

        def rand_cell(r=None):
            for _ in range(500):
                if r is None:
                    r_ = int(rng.integers(nr))
                else:
                    r_ = r
                x0, y0, x1, y1 = rects[r_]
                c = (int(rng.integers(x0, x1)), int(rng.integers(y0, y1)))
                if c not in used:
                    return c
            return None

        lms = []
        for r in range(nr):
            for _ in range(int(rng.integers(1, 3))):
                c = rand_cell(r)
                used.add(c)
                lms.append((c[0], c[1], int(rng.integers(NLM))))
        self.lms = np.array(lms)

        tc, tcol = int(rng.integers(NC)), int(rng.integers(NCOL))
        objs = []   # (x, y, cls, color)
        tl = -1
        if tier == "relational":
            L = self.lms[int(rng.integers(len(self.lms)))]
            tl = int(L[2])
            ok = False
            for _ in range(60):
                c = (int(L[0] + rng.integers(-1, 2)), int(L[1] + rng.integers(-1, 2)))
                if (0 <= c[0] < N and 0 <= c[1] < N and room[c] == room[L[0], L[1]]
                        and c not in used and self.near_lm(c[0], c[1]) == tl):
                    ok = True
                    break
            if not ok:
                return False
        else:
            c = rand_cell()
        used.add(c)
        objs.append((c[0], c[1], tc, tcol))
        for _ in range(2):
            if tier == "attribute":
                c = rand_cell()
                col = int(rng.choice([k for k in range(NCOL) if k != tcol]))
                cl = tc
            elif tier == "relational":
                c = None
                for _ in range(300):
                    q = rand_cell()
                    cheb = np.maximum(np.abs(self.lms[:, 0] - q[0]), np.abs(self.lms[:, 1] - q[1]))
                    if not ((self.lms[:, 2] == tl) & (cheb <= 3)).any():
                        c = q
                        break
                if c is None:
                    return False
                col, cl = int(rng.integers(NCOL)), tc
            else:
                c = rand_cell()
                g = tc // 4
                cl = int(rng.choice([k for k in range(4 * g, 4 * g + 4) if k != tc]))
                col = int(rng.integers(NCOL))
            used.add(c)
            objs.append((c[0], c[1], cl, col))
        for _ in range(P["n_fill"]):
            c = rand_cell()
            used.add(c)
            cl = int(rng.choice([k for k in range(NC) if k != tc]))
            objs.append((c[0], c[1], cl, int(rng.integers(NCOL))))
        o = np.array(objs)
        self.ox, self.oy, self.ocls, self.ocol = o[:, 0], o[:, 1], o[:, 2], o[:, 3]
        self.no = len(o)
        self.olm = np.array([self.near_lm(x, y) for x, y in zip(self.ox, self.oy)])
        self.oroom = room[self.ox, self.oy]
        self.oroof = self.roof[self.ox, self.oy]
        self.ocell = self.ox * N + self.oy
        self.query = Query(tier, tc, tcol, tl)
        # start cell: far enough from the target
        tcell = self.ocell[0]
        far = np.flatnonzero(self.room_cells.ravel() & (D[tcell] >= 12))
        if len(far) == 0:
            return False
        s = int(rng.choice(far))
        self.start = (s // N, s % N)
        self.opt = float(D[s, tcell])
        # perception randomness, drawn once (common random numbers across systems)
        NP = 4
        self.u_conf = rng.random((NP, self.no))
        self.u_other = rng.integers(1, 4, (NP, self.no))
        self.u_col = rng.random((NP, self.no))
        self.z_a = rng.standard_normal((NP, self.no))
        self.z_g = rng.standard_normal((NP, self.no))
        return True

    def near_lm(self, x, y):
        """Type of the nearest landmark within Chebyshev distance 2, else -1."""
        cheb = np.maximum(np.abs(self.lms[:, 0] - x), np.abs(self.lms[:, 1] - y))
        i = int(np.argmin(cheb))
        return int(self.lms[i, 2]) if cheb[i] <= 2 else -1

    def qpos(self, j):
        b = self.P["res"]
        return (min(N - 1, (int(self.ox[j]) // b) * b + b // 2),
                min(N - 1, (int(self.oy[j]) // b) * b + b // 2))

    def region(self, x, y, half):
        """Flat indices of room cells in the block of half-width `half` around (x, y)."""
        m = np.zeros((N, N), bool)
        m[max(0, x - half): x + half + 1, max(0, y - half): y + half + 1] = True
        return np.flatnonzero((m & self.room_cells).ravel())


# ---------------------------------------------------------------- channels
def nl_encode(entries, intent, world, coords):
    """Templated natural-language message -> list of word tokens."""
    t = []
    if intent is not None:
        t += ["i", "am", "heading", "to", "the", world.room_names[intent], "."]
    for k, e in enumerate(entries):
        t += ["i", "see", "a"] if k == 0 else ["and", "a"]
        if e["color"] >= 0:
            t.append(COLORS[e["color"]])
        t.append(CLASSES[e["label"]])
        if e["lm"] >= 0:
            t += ["near", "the", LANDMARKS[e["lm"]]]
        if coords:
            t += ["at", str(e["x"]), str(e["y"])]
        t += ["in", "the", world.room_names[e["room"]]]
    return t


def nl_corrupt(tokens, p, world, rng):
    out = []
    for w in tokens:
        if w in world.room_names and rng.random() < p:      # wrong-room reference
            others = [r for r in world.room_names if r != w]
            w = others[int(rng.integers(len(others)))]
        if w != "." and rng.random() < p:                    # word dropout
            continue
        out.append(w)
    return out


def nl_parse(tokens, world):
    """Rule-based keyword parser (the mock language model's reading side)."""
    entries, intent = [], None
    cur, pend_col = None, -1

    def fin(e):
        if e is None:
            return
        nums = e.pop("nums")
        if len(nums) >= 2 and 0 <= nums[0] < N and 0 <= nums[1] < N:
            e["x"], e["y"] = nums[0], nums[1]
        elif e["room"] < 0:
            return
        entries.append(e)

    for w in tokens:
        if w in CLASSES:
            fin(cur)
            cur = dict(label=CLASSES.index(w), color=pend_col, lm=-1, room=-1, nums=[])
            pend_col = -1
        elif w in COLORS:
            pend_col = COLORS.index(w)
        elif w in LANDMARKS:
            if cur is not None:
                cur["lm"] = LANDMARKS.index(w)
        elif w.isdigit():
            if cur is not None:
                cur["nums"].append(int(w))
        elif w in world.room_names:
            r = world.room_names.index(w)
            if cur is None:
                intent = r
            else:
                cur["room"] = r
                fin(cur)
                cur = None
    fin(cur)
    return entries, intent


def sym_encode(entries, intent_xy, variant):
    """Fixed-schema tuples. sym: (S, class, x, y); sym_attr adds colour and landmark ids;
    sym_score adds the sender's confidence."""
    msg = []
    if intent_xy is not None:
        msg.append(["G", intent_xy[0], intent_xy[1]])
    for e in entries:
        t = ["S", e["label"], e["x"], e["y"]]
        if variant == "sym_attr":
            t += [e["color"], e["lm"]]
        elif variant == "sym_score":
            t += [round(e["score"], 2)]
        msg.append(t)
    return msg


def sym_corrupt(msg, p, rng):
    out = []
    for t in msg:
        t = list(t)
        ix = 1 if t[0] == "G" else 2
        if rng.random() < p:                                  # wrong-location reference
            t[ix], t[ix + 1] = int(rng.integers(N)), int(rng.integers(N))
        for i in range(1, len(t)):                            # field erasure
            if rng.random() < p:
                t[i] = None
        out.append(t)
    return out


def sym_parse(msg, variant):
    entries, intent_xy = [], None
    for t in msg:
        if t[0] == "G":
            if t[1] is not None and t[2] is not None:
                intent_xy = (t[1], t[2])
            continue
        if any(v is None for v in t[1:4]):
            continue
        e = dict(label=t[1], x=t[2], y=t[3], color=-1, lm=-2, room=-1)
        if variant == "sym_attr":
            e["color"] = -1 if t[4] is None else t[4]
            e["lm"] = -2 if t[5] is None else t[5]
        elif variant == "sym_score":
            if t[4] is None:
                continue
            e["score"] = t[4]
        entries.append(e)
    return entries, intent_xy


# ---------------------------------------------------------------- agents
class Robot:
    def __init__(self, kind, world, P, policy):
        self.kind, self.w, self.P, self.policy = kind, world, P, policy
        self.x, self.y = world.start
        self.sensed = np.zeros((N, N), bool)
        self.ever = np.zeros((N, N), bool)
        self.npass = 0
        self.seen = set()          # objects evaluated in the current pass
        self.cands = {}            # own candidates: obj -> score
        self.rejected = set()
        self.remote = []           # [score, region cell indices]
        self.outbox = {}           # obj -> entry (aerial sightings not yet sent)
        self.reported = set()
        self.busy, self.busy_obj = 0, -1
        self.intent, self.sent_intent, self.mate_intent = None, None, None
        self.goal_xy = None
        self.fgoal = None
        self.yields = True
        self.last_send = -10 ** 6

    # -- sensing
    def sense(self):
        w, P = self.w, self.P
        if self.kind == "G":
            r = P["r_ground"]
            rid = w.room[self.x, self.y]
            x0, x1, y0, y1 = max(0, self.x - r), self.x + r + 1, max(0, self.y - r), self.y + r + 1
            if rid >= 0:
                m = w.room[x0:x1, y0:y1] == rid
                self.sensed[x0:x1, y0:y1] |= m
                self.ever[x0:x1, y0:y1] |= m
                vis = ((np.abs(w.ox - self.x) <= r) & (np.abs(w.oy - self.y) <= r) & (w.oroom == rid))
            else:
                vis = np.zeros(w.no, bool)
        else:
            r = P["r_air"]
            x0, x1, y0, y1 = max(0, self.x - r), self.x + r + 1, max(0, self.y - r), self.y + r + 1
            m = ~w.roof[x0:x1, y0:y1]
            self.sensed[x0:x1, y0:y1] |= m
            self.ever[x0:x1, y0:y1] |= m
            vis = (np.abs(w.ox - self.x) <= r) & (np.abs(w.oy - self.y) <= r) & (~w.oroof)
        for j in np.flatnonzero(vis):
            j = int(j)
            if j in self.seen:
                continue
            self.seen.add(j)
            self.evaluate(j)

    def evaluate(self, j):
        w, P, q = self.w, self.P, self.w.query
        p = min(self.npass, 3)
        if j in self.rejected:
            return
        if self.kind == "G":
            s = q.score(w.ocls[j], w.ocol[j], w.olm[j]) + P["noise"] * P["sig_g"] * w.z_g[p, j]
            if s >= P["tau_g"]:
                self.cands[j] = s
            else:
                self.cands.pop(j, None)
            return
        label = int(w.ocls[j])
        if w.u_conf[p, j] < P["noise"] * P["p_conf"]:
            g = label // 4
            label = 4 * g + (label - 4 * g + int(w.u_other[p, j])) % 4
        color = int(w.ocol[j]) if w.u_col[p, j] < P["p_col"] else -1
        qx, qy = w.qpos(j)
        lm = w.near_lm(qx, qy)
        nz = P["noise"] * P["sig_a"] * w.z_a[p, j]
        full = q.score(label, color, lm) + nz
        if full >= P["tau_send"]:
            self.cands[j] = full
        else:
            self.cands.pop(j, None)
        if q.class_score(label) + nz >= P["tau_send"] and j not in self.reported:
            self.outbox[j] = dict(label=label, color=color, lm=lm, x=qx, y=qy,
                                  room=int(w.oroom[j]), score=full)

    # -- motion helpers
    def step_ground(self, goal):
        w = self.w
        D = w.D
        here = self.x * N + self.y
        d = D[here, goal]
        if d == 0:
            return
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < N and 0 <= ny < N and w.free[nx, ny] and D[nx * N + ny, goal] == d - 1:
                self.x, self.y = nx, ny
                return

    def step_air(self, gx, gy):
        for _ in range(self.P["air_speed"]):
            if self.x != gx:
                self.x += 1 if gx > self.x else -1
            elif self.y != gy:
                self.y += 1 if gy > self.y else -1

    def random_move(self, rng):
        w = self.w
        for _ in range(1 if self.kind == "G" else self.P["air_speed"]):
            opts = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < N and 0 <= ny < N and (self.kind == "A" or w.free[nx, ny]):
                    opts.append((nx, ny))
            self.x, self.y = opts[int(rng.integers(len(opts)))]

    def dist_to(self, cells):
        if self.kind == "G":
            return self.w.D[self.x * N + self.y, cells]
        return np.abs(cells // N - self.x) + np.abs(cells % N - self.y)

    def frontier(self):
        """Nearest unsensed cell, with a penalty on the teammate's announced room."""
        w = self.w
        m = w.room_cells & ~self.sensed
        if self.kind == "A":
            m &= ~w.roof
        if self.fgoal is not None and m.ravel()[self.fgoal]:
            return self.fgoal          # keep the current frontier goal until it is sensed
        cells = np.flatnonzero(m.ravel())
        if len(cells) == 0:
            return None
        cost = self.dist_to(cells).astype(float)
        if self.mate_intent is not None and self.yields:
            cost = cost + self.P["intent_pen"] * (w.room.ravel()[cells] == self.mate_intent)
        self.fgoal = int(cells[int(np.argmin(cost))])
        return self.fgoal

    def new_pass(self):
        self.sensed[:] = False
        self.seen.clear()
        self.npass += 1

    # -- one decision; returns True if the target was verified
    def act(self, rng):
        w, P = self.w, self.P
        if self.busy > 0:
            self.busy -= 1
            if self.busy == 0:
                j = self.busy_obj
                if j == 0:
                    return True
                self.rejected.add(j)
                self.cands.pop(j, None)
            return False
        self.intent = None
        if self.kind == "G":
            if self.cands:
                js = list(self.cands)
                d = w.D[self.x * N + self.y, w.ocell[js]]
                k = int(np.argmin(d))
                if d[k] <= 1:
                    self.busy, self.busy_obj = P["inspect_g"], js[k]
                else:
                    self.step_ground(int(w.ocell[js[k]]))
                return False
            if self.policy == "random":
                self.random_move(rng)
                return False
            best, best_u = None, -1e9
            keep = []
            flat = self.sensed.ravel()
            for c in self.remote:
                left = c[1][~flat[c[1]]]
                if len(left) == 0:
                    continue
                keep.append(c)
                d = self.dist_to(left)
                k = int(np.argmin(d))
                u = c[0] - d[k] / P["dist_scale"]
                if u > best_u:
                    best_u, best = u, int(left[k])
            self.remote = keep
            goal = best if best is not None else self.frontier()
            if goal is None:
                self.new_pass()
                return False
            self.intent = int(w.room.ravel()[goal])
            self.goal_xy = (goal // N, goal % N)
            self.step_ground(goal)
            return False
        # aerial
        if self.policy == "random":
            self.random_move(rng)
            return False
        goal = self.frontier()
        if goal is not None:
            self.intent = int(w.room.ravel()[goal])
            self.goal_xy = (goal // N, goal % N)
            self.step_air(goal // N, goal % N)
            return False
        if self.cands:
            j = max(self.cands, key=lambda k: (self.cands[k], -k))
            qx, qy = w.qpos(j)
            if (self.x, self.y) == (qx, qy):
                self.busy, self.busy_obj = P["inspect_a"], j
            else:
                self.step_air(qx, qy)
            return False
        self.new_pass()
        return False


SYSTEMS = ["nl", "sym", "nocomm", "single", "random", "oracle", "nl_coords", "sym_attr", "sym_score"]


def deliver(sender, recv, world, system, P, crng, stats):
    """Compose, (maybe) corrupt, parse and integrate one message from sender to recv."""
    q = world.query
    M = P["M"]
    items = sorted(sender.outbox.items(), key=lambda kv: (-kv[1]["score"], kv[0]))[:M]
    intent = sender.intent if sender.intent != sender.sent_intent else None
    if not items and intent is None:
        return
    entries = [e for _, e in items]
    for j, _ in items:
        del sender.outbox[j]
        sender.reported.add(j)
    if intent is not None:
        sender.sent_intent = intent
    half = P["res"] // 2
    if system == "oracle":
        parsed, p_intent = entries, intent
    elif system in ("nl", "nl_coords"):
        toks = nl_encode(entries, intent, world, system == "nl_coords")
        stats["msgs"] += 1
        stats["tokens"] += sum(1 for t in toks if t != ".")
        if P["corrupt"] > 0:
            toks = nl_corrupt(toks, P["corrupt"], world, crng)
        parsed, p_intent = nl_parse(toks, world)
    else:
        msg = sym_encode(entries, sender.goal_xy if intent is not None else None, system)
        stats["msgs"] += 1
        stats["tokens"] += sum(len(t) for t in msg)
        if P["corrupt"] > 0:
            msg = sym_corrupt(msg, P["corrupt"], crng)
        parsed, ixy = sym_parse(msg, system)
        p_intent = None
        if ixy is not None and world.room[ixy] >= 0:
            p_intent = int(world.room[ixy])
    if p_intent is not None:
        recv.mate_intent = p_intent
    if recv.kind != "G":
        return
    for e in parsed:
        if "x" in e:
            cells = world.region(e["x"], e["y"], half)
        else:
            cells = np.flatnonzero((world.room == e["room"]).ravel())
        if len(cells) == 0:
            continue
        s = e["score"] if system == "sym_score" else q.score(e["label"], e["color"], e["lm"])
        if s >= P["tau_r"]:
            recv.remote.append([s, cells])


def run_episode(seed, tier, ep, system, P):
    tix = TIERS.index(tier)
    world = World(np.random.default_rng([seed, tix, ep, 1]), tier, P)
    arng = np.random.default_rng([seed, tix, ep, 2])   # random-walk moves
    crng = np.random.default_rng([seed, tix, ep, 3])   # message corruption
    team = "G" if system == "single" else P["team"]
    policy = "random" if system == "random" else "frontier"
    robots = [Robot(k, world, P, policy) for k in team]
    for i, r in enumerate(robots):
        r.yields = not (P["prio"] and i == 0)
    comm = system not in ("nocomm", "single", "random") and len(robots) == 2
    K = 1 if system == "oracle" else P["K"]
    if system == "oracle":
        P = dict(P, M=99)
    stats = dict(msgs=0, tokens=0)
    success, t_found, finder = 0, P["cap"], ""
    for t in range(1, P["cap"] + 1):
        for r in robots:
            r.sense()
        if comm:
            for i, r in enumerate(robots):
                if t - r.last_send >= K:
                    before = stats["msgs"]
                    n_out = len(r.outbox)
                    deliver(r, robots[1 - i], world, system, P, crng, stats)
                    if stats["msgs"] > before or (system == "oracle" and n_out):
                        r.last_send = t
        done = False
        for r in robots:
            if r.act(arng):
                done, finder = True, r.kind
        if done:
            success, t_found = 1, t
            break
    room_cells = world.room_cells
    if len(robots) == 2:
        a, b = robots[0].ever & room_cells, robots[1].ever & room_cells
        overlap = float((a & b).sum()) / max(1, int((a | b).sum()))
    else:
        overlap = 0.0
    spl = success * min(1.0, world.opt / t_found)
    return dict(success=success, steps=t_found, spl=spl, msgs=stats["msgs"], tokens=stats["tokens"],
                overlap=overlap, aerial_find=int(finder == "A"), roofed_target=int(world.oroof[0]),
                tier=tier)
