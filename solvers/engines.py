"""Stellar engine modules — Layer 3 (counterexample), 3.5 (invertibility),
and 4 (tactic sweep).

Imported by solvers/stellar_v1.py.  Kept in a separate module so the
top-level solver file stays readable and so we can iterate on the engines
without touching the BFS / closure-graph plumbing.

Each engine returns either a Lean code string ready to submit (for
proof-side engines) or a (n, table) tuple (for counterexample engines),
or None if it cannot solve the problem.

For the competition submission, all of this code will be inlined back
into a single solver.py.  During development we keep them separate.
"""
from __future__ import annotations

import re
from itertools import product as iproduct
from typing import Callable

# ─────────────────────────────────────────────────────────────────────────────
# Equation analysis utilities
# ─────────────────────────────────────────────────────────────────────────────


def variables_of(eq: str) -> list[str]:
    """Return the list of single-letter variables appearing in an equation,
    in order of first appearance (left-to-right)."""
    seen: set[str] = set()
    out: list[str] = []
    for m in re.finditer(r"\b([a-z])\b", eq):
        v = m.group(1)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def split_eq(eq: str) -> tuple[str, str]:
    """Split `lhs = rhs` into (lhs, rhs), each stripped."""
    lhs, rhs = eq.split("=", 1)
    return lhs.strip(), rhs.strip()


def analyse(eq: str) -> dict:
    """Return structural info about an equation:
        lhs / rhs        : str
        all_vars         : list of vars in declaration order
        lhs_vars         : set of vars on LHS
        rhs_vars         : set of vars on RHS
        lhs_only         : LHS-only vars (don't appear on RHS) — pivot candidates
        rhs_only         : RHS-only vars — typically free quantification
        lhs_atomic       : True if LHS is a single variable
    """
    lhs, rhs = split_eq(eq)
    all_vars = variables_of(eq)
    lhs_vs = set(variables_of(lhs))
    rhs_vs = set(variables_of(rhs))
    return {
        "lhs": lhs,
        "rhs": rhs,
        "all_vars": all_vars,
        "lhs_vars": lhs_vs,
        "rhs_vars": rhs_vs,
        "lhs_only": lhs_vs - rhs_vs,
        "rhs_only": rhs_vs - lhs_vs,
        "lhs_atomic": len(lhs) == 1 and lhs.isalpha(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Lean code wrapper (mirrors solvers/stellar_v1.make_true_code)
# ─────────────────────────────────────────────────────────────────────────────


def lean_true(proof_body: str) -> str:
    """Wrap a tactic body inside the standard `def submission`.

    Caller's body is inserted after `intro G _ h` and before the closing
    of the `by` block.  The body should NOT include `intro` for G; it
    SHOULD include any further intros for the goal's variables.
    """
    indented = "\n".join(("  " + l) if l.strip() else "" for l in proof_body.strip().split("\n"))
    return (
        "import JudgeProblem\n"
        "import Mathlib.Tactic\n\n"
        "def submission : Goal := by\n"
        "  intro G _ h\n"
        f"{indented}\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Layer 4 — Tactic sweep
# ─────────────────────────────────────────────────────────────────────────────
#
# Strategy: ordered list of tactic-body candidates, each tried sequentially
# against the judge.  Order is empirical — earlier candidates have higher
# historical hit rate from EULER's data.
#
# Categories (in order of attempt):
#   1. Pure tactic blasts (grind / simp_all / aesop) — single line, catch trivials
#   2. h-specialization + grind  (most common pattern: have k := h x x x; grind)
#   3. simp only [h] / [h, h.symm] / [← h] — quasi-constant pattern
#   4. Reverse-h-lemma + grind  (Ježek pattern: have h' = h.symm; grind)
#   5. Free-var collapse + grind (Tao lemma synthesis)
#   6. calc bootstrap with single rewrite step

def build_tactic_candidates(eq1: str, eq2: str) -> list[str]:
    v1 = variables_of(eq1)
    v2 = variables_of(eq2)
    info1 = analyse(eq1)
    lhs1, rhs1 = info1["lhs"], info1["rhs"]
    free1 = sorted(info1["lhs_only"] | info1["rhs_only"])
    bound1 = [v for v in v1 if v not in free1]
    intro = "intro " + " ".join(v2) if v2 else ""
    candidates: list[str] = []

    # ── 1. Pure tactic blasts ─────────────────────────────────────────────
    candidates.append(f"{intro}\nsimp only [h]")
    candidates.append(f"{intro}\nsimp_all only [h]")
    candidates.append(f"{intro}\ngrind")
    candidates.append(f"{intro}\naesop")
    candidates.append(f"{intro}\nsimp_all")
    candidates.append(f"{intro}\nfirst | rfl | (rw [h] <;> rfl) | grind")

    # ── 2. h-specialization + grind ───────────────────────────────────────
    # Self-application (column of one variable, length len(v1))
    if v1 and v2:
        for a in v2[:3]:
            col = " ".join([a] * len(v1))
            candidates.append(f"{intro}\nhave k := h {col}\ngrind")

    # Mixed: lead var then column of another
    if len(v1) >= 2 and len(v2) >= 2:
        for lead in v2[:2]:
            for body_var in v2[:2]:
                if lead == body_var:
                    continue
                rest = " ".join([body_var] * (len(v1) - 1))
                candidates.append(f"{intro}\nhave k := h {lead} {rest}\ngrind")

    # Two h's at different specializations
    if len(v1) >= 2 and len(v2) >= 2:
        a, b = v2[0], v2[1]
        col_a = " ".join([a] * len(v1))
        col_b = " ".join([b] * len(v1))
        candidates.append(
            f"{intro}\nhave k1 := h {col_a}\nhave k2 := h {col_b}\ngrind"
        )

    # ── 3. simp variants with reverse rewrite ─────────────────────────────
    if v1:
        quant = " ".join(f"({v} : G)" for v in v1)
        args = " ".join(v1)
        h_rev = (
            f"have h' : ∀ {quant}, {rhs1} = {lhs1} := "
            f"fun {args} => (h {args}).symm"
        )
        candidates.append(f"{intro}\n{h_rev}\nsimp only [h']")
        candidates.append(f"{intro}\n{h_rev}\ngrind")

    # ── 4. Compound-term feed (x ↦ x◇x) ──────────────────────────────────
    if len(v1) >= 2 and v2:
        a = v2[0]
        col = " ".join([a] * len(v1))
        for pos in range(min(len(v1), 3)):
            args = [a] * len(v1)
            args[pos] = f"({a} ◇ {a})"
            candidates.append(
                f"{intro}\nhave k1 := h {col}\nhave k2 := h {' '.join(args)}\ngrind"
            )

    # ── 5. Free-var collapse + grind (Tao synthesis) ─────────────────────
    if bound1 and free1:
        bv = bound1[0]
        for keep_idx in range(len(free1)):
            specialized = rhs1
            for i, fv in enumerate(free1):
                if i != keep_idx:
                    specialized = re.sub(rf"\b{fv}\b", bv, specialized)
            renamed = specialized
            renamed = re.sub(rf"\b{bv}\b", "__A__", renamed)
            renamed = re.sub(rf"\b{free1[keep_idx]}\b", "__B__", renamed)
            renamed = renamed.replace("__A__", "a").replace("__B__", "b")
            have_lem = (
                f"have lem : ∀ (a b : G), a = {renamed} := by intro a b; grind"
            )
            candidates.append(f"{intro}\n{have_lem}\ngrind")

    # ── 6. Final fall-throughs ────────────────────────────────────────────
    candidates.append(f"{intro}\nall_goals first | rfl | grind | aesop")
    candidates.append(f"{intro}\nfirst | grind | (simp_all; grind) | aesop")

    # Dedup while preserving order.
    seen: set[str] = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def tactic_sweep(eq1: str, eq2: str, judge_call: Callable[[str], dict],
                 max_attempts: int = 30) -> bool:
    """Try up to `max_attempts` tactic candidates against the judge.
    Returns True iff one is accepted.
    """
    candidates = build_tactic_candidates(eq1, eq2)
    for proof in candidates[:max_attempts]:
        result = judge_call(lean_true(proof))
        if result.get("status") == "accepted":
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3 — Counterexample engines (cheap families, plan §2.3.1–2.3.9)
# ─────────────────────────────────────────────────────────────────────────────
#
# Each engine takes parsed equations and returns (n, table) on hit, or None.
# All are deterministic enumeration over finite parameter spaces.
#
# Order matters — `find_counterexample_cheap` runs them ms→s, returning
# the first hit so the cost stays bounded.

def parse_equation(eq: str):
    """Compile `eq` ("x = (y ◇ z) ◇ ..." form) into evaluators.
    Returns (variables: list[str], lhs_fn: env→int, rhs_fn: env→int).
    """
    seen: set[str] = set()
    variables: list[str] = []
    for v in re.findall(r"\b([a-z])\b", eq):
        if v not in seen:
            seen.add(v)
            variables.append(v)
    lhs_str, rhs_str = eq.split("=", 1)

    def _to_expr(s: str):
        s = s.strip()
        while len(s) >= 2 and s[0] == "(" and s[-1] == ")":
            depth = 0
            matched = True
            for i, c in enumerate(s):
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                if depth == 0 and i < len(s) - 1:
                    matched = False
                    break
            if matched:
                s = s[1:-1].strip()
            else:
                break
        depth = 0
        last_op = -1
        for i, c in enumerate(s):
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif c == "◇" and depth == 0:
                last_op = i
        if last_op >= 0:
            left = _to_expr(s[:last_op])
            right = _to_expr(s[last_op + 1:])
            return lambda env, l=left, r=right: env["op"](l(env), r(env))
        s = s.strip()
        if len(s) == 1 and s in seen:
            return lambda env, v=s: env[v]
        raise ValueError(f"cannot parse: {s!r}")

    return variables, _to_expr(lhs_str), _to_expr(rhs_str)


def check_equation(variables: list[str], lhs_fn, rhs_fn, n: int, op) -> bool:
    """True iff lhs_fn ≡ rhs_fn for all assignments in Fin n."""
    for vals in iproduct(range(n), repeat=len(variables)):
        env = {"op": op}
        for v, val in zip(variables, vals):
            env[v] = val
        if lhs_fn(env) != rhs_fn(env):
            return False
    return True


# §2.3.8 Structured base — paper §3.1 finite-sec specialised tables
def _structured_tables(n: int) -> list[list[list[int]]]:
    """Hand-picked diverse n×n magma tables to try first."""
    out: list[list[list[int]]] = []
    # Constant: op(a,b) = c
    for c in range(n):
        out.append([[c] * n for _ in range(n)])
    # Left-projection: op(a,b) = a
    out.append([[i] * n for i in range(n)])
    # Right-projection: op(a,b) = b
    out.append([list(range(n)) for _ in range(n)])
    # Cyclic: op(a,b) = (a+b) mod n
    out.append([[(i + j) % n for j in range(n)] for i in range(n)])
    # Anti-cyclic: op(a,b) = (a-b) mod n
    out.append([[(i - j) % n for j in range(n)] for i in range(n)])
    # Constant-row tables: row i is all-i
    for i in range(n):
        out.append([[i] * n for _ in range(n)])
    # Sparse zero-except-one
    for r in range(n):
        for c in range(n):
            for v in range(1, n):
                t = [[0] * n for _ in range(n)]
                t[r][c] = v
                out.append(t)
    return out


def search_structured(vs1, lhs1, rhs1, vs2, lhs2, rhs2, max_n: int = 6):
    """§2.3.8 + §2.3.9 light. Try structured tables on Fin 2..max_n."""
    for n in range(2, max_n + 1):
        for table in _structured_tables(n):
            op = lambda a, b, t=table: t[a][b]
            if check_equation(vs1, lhs1, rhs1, n, op):
                if not check_equation(vs2, lhs2, rhs2, n, op):
                    return n, table
    return None


# §2.3.2 Linear over Z/p — paper §3.2 linear-sec
def search_linear_zp(vs1, lhs1, rhs1, vs2, lhs2, rhs2,
                     primes=(2, 3, 5, 7)):
    """`a*i + b*j + c` mod p, ~503 candidates total."""
    for p in primes:
        for a, b, c in iproduct(range(p), repeat=3):
            op = lambda x, y, a=a, b=b, c=c, p=p: (a*x + b*y + c) % p
            if check_equation(vs1, lhs1, rhs1, p, op):
                if not check_equation(vs2, lhs2, rhs2, p, op):
                    return p, [[(a*i + b*j + c) % p for j in range(p)] for i in range(p)]
    return None


# §2.3.3 Bilinear extension — extension of §3.2
def search_bilinear_ext(vs1, lhs1, rhs1, vs2, lhs2, rhs2, primes=(3, 5)):
    """`a*i + b*j + c*ij + d` mod p, ~706 candidates."""
    for p in primes:
        for a, b, c, d in iproduct(range(p), repeat=4):
            table = [[(a*i + b*j + c*i*j + d) % p for j in range(p)] for i in range(p)]
            op = lambda x, y, t=table: t[x][y]
            if check_equation(vs1, lhs1, rhs1, p, op):
                if not check_equation(vs2, lhs2, rhs2, p, op):
                    return p, table
    return None


# §2.3.4 Quadratic — paper §3.2 remark
def search_quadratic_zp(vs1, lhs1, rhs1, vs2, lhs2, rhs2, primes=(3, 5)):
    """`a*i² + b*j² + c*ij + d*i + e*j + f` mod p. p=3: 729; p=5: 15625."""
    for p in primes:
        for a, b, c, d, e, f in iproduct(range(p), repeat=6):
            table = [[(a*i*i + b*j*j + c*i*j + d*i + e*j + f) % p
                      for j in range(p)] for i in range(p)]
            op = lambda x, y, t=table: t[x][y]
            if check_equation(vs1, lhs1, rhs1, p, op):
                if not check_equation(vs2, lhs2, rhs2, p, op):
                    return p, table
    return None


# §2.3.5 Translation-invariant (cyclic)
def search_cyclic(vs1, lhs1, rhs1, vs2, lhs2, rhs2, max_n: int = 12):
    """Successor: op(a,b)=(a+k)%n  and  op(a,b)=(b+k)%n."""
    for n in range(2, max_n):
        for k in range(1, n):
            # Left successor
            table = [[(i + k) % n for _ in range(n)] for i in range(n)]
            op = lambda x, y, t=table: t[x][y]
            if check_equation(vs1, lhs1, rhs1, n, op):
                if not check_equation(vs2, lhs2, rhs2, n, op):
                    return n, table
            # Right successor
            table = [[(j + k) % n for j in range(n)] for _ in range(n)]
            op = lambda x, y, t=table: t[x][y]
            if check_equation(vs1, lhs1, rhs1, n, op):
                if not check_equation(vs2, lhs2, rhs2, n, op):
                    return n, table
    return None


# §2.3.6 Z_p × Z_q product
def search_zp_zq_product(vs1, lhs1, rhs1, vs2, lhs2, rhs2, n_range=(4, 10)):
    """Product magmas Z_p × Z_q with linear ops in each factor."""
    for n in range(n_range[0], n_range[1]):
        for p in range(2, n):
            if n % p:
                continue
            q = n // p
            for a1, a2, b1, b2 in iproduct(range(p), range(p), range(q), range(q)):
                if a1 == 0 and a2 == 0 and b1 == 0 and b2 == 0:
                    continue
                table = [[0] * n for _ in range(n)]
                for i in range(n):
                    for j in range(n):
                        r, s = i // q, i % q
                        t, u = j // q, j % q
                        table[i][j] = ((a1*r + a2*t) % p) * q + ((b1*s + b2*u) % q)
                op = lambda x, y, tt=table: tt[x][y]
                if check_equation(vs1, lhs1, rhs1, n, op):
                    if not check_equation(vs2, lhs2, rhs2, n, op):
                        return n, table
    return None


# §2.3.9 Random — fallback for what structured/linear miss
def search_random_fin(vs1, lhs1, rhs1, vs2, lhs2, rhs2,
                      sizes=((3, 19683), (4, 30000), (5, 30000), (6, 5000)),
                      time_budget: float = 15.0):
    """Random sample on Fin n with per-size budgets. Stops at time_budget total."""
    import random
    import time
    rng = random.Random(0xC0FFEE)
    deadline = time.time() + time_budget
    for n, attempts in sizes:
        for _ in range(attempts):
            if time.time() > deadline:
                return None
            table = [[rng.randrange(n) for _ in range(n)] for _ in range(n)]
            op = lambda x, y, t=table: t[x][y]
            if check_equation(vs1, lhs1, rhs1, n, op):
                if not check_equation(vs2, lhs2, rhs2, n, op):
                    return n, table
    return None


def find_counterexample_cheap(eq1: str, eq2: str):
    """Run the cheap counterexample families in priority order.

    Order: structured → linear_zp → cyclic → bilinear → quadratic → product →
           near_miss → backtrack → random.

    All families are deterministic enumeration (or seeded random) — they
    target whole equation classes, never single problems.

    Returns (n, table) on hit, else None.
    """
    try:
        vs1, lhs1, rhs1 = parse_equation(eq1)
        vs2, lhs2, rhs2 = parse_equation(eq2)
    except Exception:
        return None

    families = [
        ("structured_8",      lambda: search_structured(vs1, lhs1, rhs1, vs2, lhs2, rhs2, max_n=8)),
        ("linear_zp",         lambda: search_linear_zp(vs1, lhs1, rhs1, vs2, lhs2, rhs2)),
        ("cyclic",            lambda: search_cyclic(vs1, lhs1, rhs1, vs2, lhs2, rhs2)),
        ("bilinear_ext",      lambda: search_bilinear_ext(vs1, lhs1, rhs1, vs2, lhs2, rhs2)),
        ("quadratic_zp",      lambda: search_quadratic_zp(vs1, lhs1, rhs1, vs2, lhs2, rhs2)),
        ("zp_zq_product",     lambda: search_zp_zq_product(vs1, lhs1, rhs1, vs2, lhs2, rhs2)),
        ("near_miss",         lambda: search_near_miss(vs1, lhs1, rhs1, vs2, lhs2, rhs2)),
        ("backtrack_fin",     lambda: search_backtrack(vs1, lhs1, rhs1, vs2, lhs2, rhs2,
                                                        sizes=(3, 4, 5), time_budget=10.0)),
        ("random_fin",        lambda: search_random_fin(vs1, lhs1, rhs1, vs2, lhs2, rhs2,
                                                        sizes=((3, 19683), (4, 50000), (5, 50000),
                                                               (6, 10000), (7, 5000), (8, 2000)),
                                                        time_budget=20.0)),
    ]
    for name, fn in families:
        result = fn()
        if result is not None:
            return result
    return None


# ── §2.3.7 Near-miss mutation: take structured models of h, flip 1-2 entries ──
def search_near_miss(vs1, lhs1, rhs1, vs2, lhs2, rhs2,
                      sizes=(3, 4, 5), mutations_per_base=80,
                      time_budget: float = 8.0):
    """Mutate structured tables that already satisfy eq1; check if violation of eq2.

    Bounded by time_budget so it doesn't dominate Stage 3 wall-clock when
    nothing helpful is found.  ~80 mutations per base × 10 bases × 3 sizes
    = 2400 trials, fits in ~5s.
    """
    import random
    import time
    rng = random.Random(0xDEADBEEF)
    deadline = time.time() + time_budget
    for n in sizes:
        if time.time() > deadline:
            return None
        bases = []
        for tbl in _structured_tables(n):
            op = lambda a, b, t=tbl: t[a][b]
            if check_equation(vs1, lhs1, rhs1, n, op):
                bases.append([row[:] for row in tbl])
        for base in bases[:10]:
            for _ in range(mutations_per_base):
                if time.time() > deadline:
                    return None
                mutated = [row[:] for row in base]
                for _ in range(rng.randint(1, 2)):
                    mi, mj = rng.randrange(n), rng.randrange(n)
                    mutated[mi][mj] = rng.randrange(n)
                op = lambda a, b, t=mutated: t[a][b]
                if check_equation(vs1, lhs1, rhs1, n, op):
                    if not check_equation(vs2, lhs2, rhs2, n, op):
                        return n, mutated
    return None


# ── SAT-style backtracking: fill table cell by cell, prune on eq1 violation ──
def search_backtrack(vs1, lhs1, rhs1, vs2, lhs2, rhs2,
                      sizes=(3, 4, 5), time_budget: float = 15.0):
    """Backtracking on Fin n: assign each cell, prune if eq1 violated by any
    fully-assigned variable tuple."""
    import time
    deadline = time.time() + time_budget
    for n in sizes:
        if time.time() > deadline:
            return None
        cells = [(i, j) for i in range(n) for j in range(n)]
        nc = n * n
        table = [[None] * n for _ in range(n)]
        vals = [0] * nc
        ci = 0
        while 0 <= ci < nc:
            if time.time() > deadline:
                return None
            i, j = cells[ci]
            if vals[ci] >= n:
                # backtrack
                table[i][j] = None; vals[ci] = 0; ci -= 1
                if ci >= 0:
                    table[cells[ci][0]][cells[ci][1]] = None
                    vals[ci] += 1
                continue
            table[i][j] = vals[ci]
            # Test eq1 with partial table — only on tuples that don't hit a None cell
            op = lambda a, b, t=table: t[a][b] if t[a][b] is not None else None
            eq1_ok = True
            for vv in iproduct(range(n), repeat=len(vs1)):
                env = {"op": op}
                for v, val in zip(vs1, vv):
                    env[v] = val
                try:
                    lv, rv = lhs1(env), rhs1(env)
                except TypeError:
                    continue  # hit a None cell, skip
                if lv is not None and rv is not None and lv != rv:
                    eq1_ok = False; break
            if eq1_ok:
                if ci == nc - 1:
                    fop = lambda a, b, t=table: t[a][b]
                    if not check_equation(vs2, lhs2, rhs2, n, fop):
                        return n, [row[:] for row in table]
                    vals[ci] += 1; table[i][j] = None
                else:
                    ci += 1
            else:
                table[i][j] = None; vals[ci] += 1
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3.5 — Invertibility sweep (Tao S/L/T pattern, plan §2.4.6)
# ─────────────────────────────────────────────────────────────────────────────
#
# Mostly grind-driven Lean blocks that scaffold S(x)=x◇x, L_y(x)=y◇x etc.
# These overlap with tactic_sweep's `grind` candidates but specifically
# materialize the helper functions Tao's ManuallyProved entries use.

def build_invertibility_candidates(eq1: str, eq2: str) -> list[str]:
    v1 = variables_of(eq1)
    v2 = variables_of(eq2)
    intro = "intro " + " ".join(v2)
    candidates = []

    # Pattern A: Define S, basic h instantiation
    if v1 and v2:
        col = " ".join([v2[0]] * len(v1))
        candidates.append(
            f"{intro}\n"
            f"let S (x : G) := x ◇ x\n"
            f"have k := h {col}\n"
            f"grind"
        )

    # Pattern B: S + L_y + two h instantiations
    if len(v1) >= 1 and len(v2) >= 2:
        a, b = v2[0], v2[1]
        candidates.append(
            f"{intro}\n"
            f"let S (x : G) := x ◇ x\n"
            f"let L (y x : G) := y ◇ x\n"
            f"have k1 := h {' '.join([a] * len(v1))}\n"
            f"have k2 := h {' '.join([b] * len(v1))}\n"
            f"grind"
        )

    # Pattern C: Idempotent helper
    if v1 and v2:
        a = v2[0]
        col = " ".join([a] * len(v1))
        candidates.append(
            f"{intro}\n"
            f"have k := h {col}\n"
            f"have idem : ∀ (x : G), x ◇ x = x := by\n"
            f"  intro x; have := h {' '.join(['x'] * len(v1))}; grind\n"
            f"grind"
        )

    # Pattern D: Commutativity helper
    if len(v2) >= 2:
        candidates.append(
            f"{intro}\n"
            f"have comm : ∀ (a b : G), a ◇ b = b ◇ a := by\n"
            f"  intro a b; grind\n"
            f"grind"
        )

    # Pattern E: Absorption helper
    if len(v2) >= 2:
        candidates.append(
            f"{intro}\n"
            f"have absorb : ∀ (a b : G), a ◇ (a ◇ b) = a ◇ b := by\n"
            f"  intro a b; grind\n"
            f"grind"
        )

    # Pattern F: T(x) = x ◇ S(x) chain
    if v1 and v2:
        a = v2[0]
        col = " ".join([a] * len(v1))
        candidates.append(
            f"{intro}\n"
            f"let S (x : G) := x ◇ x\n"
            f"let T (x : G) := x ◇ S x\n"
            f"have k := h {col}\n"
            f"grind"
        )

    return candidates


def invertibility_sweep(eq1: str, eq2: str, judge_call: Callable[[str], dict]) -> bool:
    candidates = build_invertibility_candidates(eq1, eq2)
    for proof in candidates:
        result = judge_call(lean_true(proof))
        if result.get("status") == "accepted":
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Layer 3.6 — Meta-closure rewriter (general engine for Class B residuals)
# ─────────────────────────────────────────────────────────────────────────────
#
# Some hard TRUE problems can't be solved by direct closure-path BFS but yield to:
#   1. Derive an auxiliary equation E_aux from h via the closure graph
#      (typically E_aux is "shape-simple": Eq40 = `x◇x = y◇y`, Eq2 = `x = y`, …)
#   2. Use E_aux to rewrite the goal at the right occurrence
#   3. `apply h` to close
#
# Example (E_3291 → E_3304, ETP's actual proof):
#   Goal: x◇x = y◇(z◇(w◇u))
#   eq40 derived from h via chain 3291→3289→3699→40 gives `∀ a b, a◇a = b◇b`
#   nth_rewrite 1 [← eq40 _ w] turns `x◇x` into `w◇w` via the universal pattern
#   apply h closes
#
# This engine searches: for each E_aux reachable from h (in our v3 closure graph),
# try (a) build E_aux via inlined chain, (b) try nth_rewrite at a few occurrences
# in both directions, (c) try `apply h` to close. Falls back to grind / aesop if
# `apply h` fails.

# "Shape-simple" priorities for auxiliary equations: prefer those with very few
# free variables (most powerful as universal rewrite rules).
_SIMPLE_AUX_PRIORITY = (
    2,    # Equation2: ∀ x y, x = y          — singleton, kills everything
    40,   # Equation40: ∀ x y, x◇x = y◇y     — most common cohomology helper
    3,    # Equation3: ∀ x, x = x◇x          — idempotent
    4,    # Equation4: ∀ x y, x = x◇y        — left-projection
    5,    # Equation5: ∀ x y, x = y◇x        — right-projection
    8,    # Equation8: ∀ x, x = x◇(x◇x)
    23,   # Equation23: ∀ x, x◇x = x
    38,   # Equation38: ∀ x y, x◇x = y◇x
    39,   # Equation39: ∀ x y, x◇x = x◇y
    41,   # Equation41: ∀ x y z, x = y◇z      — constant-magma signal
    42,   # Equation42: ∀ x y, x◇y = y◇x      — commutativity
    43,   # Equation43: ∀ x y z, x◇y = z◇x
    46,   # Equation46: ∀ x y z, x◇y = z◇w
)


def _aux_chain_proof(adj: dict, src: int, aux: int, max_depth: int = 6,
                       lambda_only: bool = True) -> str | None:
    """Build the inlined `have h := ...` chain that promotes h (= E_src) to E_aux.

    With lambda_only=True (default), the BFS only traverses lambda/term edges
    — these inline cleanly via `have h := (body)` without needing type annotations
    or fragile tactic-body composition.

    Returns the body of a tactic block that, when run after `intro G _ h`,
    produces a new `h` of type matching E_aux.  Returns None if no path
    exists in adj.
    """
    import collections as _c
    if src == aux:
        return None  # Trivial; no chain needed
    if src not in adj:
        return None
    seen = {src}
    queue = _c.deque([(src, [src])])
    path: list[int] | None = None
    while queue:
        u, p = queue.popleft()
        if len(p) > max_depth:
            continue
        for entry in adj.get(u, ()):
            v = entry[0]
            kind = entry[2]
            if lambda_only and kind == "tactic":
                continue
            if v == aux:
                path = p + [v]
                queue.clear()
                break
            if v not in seen:
                seen.add(v)
                queue.append((v, p + [v]))
        if path:
            break
    if path is None:
        return None

    # Now build the chain. For each step, we need (body, kind, thm_name).
    lines: list[str] = []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        edge = None
        for entry in adj.get(a, ()):
            if entry[0] == b:
                edge = entry  # (tgt, body, kind, thm)
                break
        if edge is None:
            return None
        body, kind = edge[1], edge[2]
        if kind == "tactic":
            # Tactic body already starts with `by ...`; strip the leading `by` and re-wrap.
            stripped = body.strip()
            if stripped.startswith("by"):
                stripped = stripped[2:].lstrip()
            body_indented = stripped.replace("\n", "\n      ")
            ed = _eqdefs_cache.get(b) if _eqdefs_cache else None
            if ed:
                vars_str, body_eq = ed
                ann = f": ∀ ({vars_str} : G), {body_eq}"
            else:
                ann = ""
            lines.append(f"have h {ann} := by\n      {body_indented}")
        else:
            # lambda or term — Lean infers
            body_indented = body.replace("\n", "\n      ")
            lines.append(f"have h := (\n      {body_indented}\n    )")
    return "\n    ".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Layer 4.5 — Superposition simulator (general engine for Class A residuals)
# ─────────────────────────────────────────────────────────────────────────────
#
# Vampire-style superposition derives new equations by combining h-instances at
# different positions: e.g. given h: x = (y◇y) ◇ ((z◇x) ◇ x), derive
#   eq12 (X0 X1 X2) : ((X0 ◇ X1) ◇ X1) = ((X2 ◇ X2) ◇ X1)  via superposition of h with itself.
#
# In pure Lean we simulate this by generating MANY `have ki := h <args>` for
# systematic argument combinations, optionally with `.symm`, then closing via
# `grind` / `aesop`.  The exponential blowup is bounded by max_total_haves.

def build_superposition_candidates(eq1: str, eq2: str, max_haves: int = 8) -> list[str]:
    """Generate candidates with up to `max_haves` h-instantiations + grind."""
    v1 = variables_of(eq1)
    v2 = variables_of(eq2)
    n = len(v1)
    intro = "intro " + " ".join(v2) if v2 else ""

    # Argument pool: goal vars + a few compound terms
    pool = list(v2)
    if v2:
        for a in v2[:2]:
            for b in v2[:2]:
                pool.append(f"({a} ◇ {b})")

    # Systematic tuples: prefer "diagonal" (all same) and "single-perturbation" patterns.
    diagonal_tuples = [tuple([v] * n) for v in v2]
    perturbation_tuples = []
    for base in v2[:3]:
        for pos in range(n):
            for swap in v2[:3]:
                if swap == base:
                    continue
                tup = [base] * n
                tup[pos] = swap
                perturbation_tuples.append(tuple(tup))
    # All distinct subset
    all_distinct = []
    if len(v2) >= n:
        from itertools import permutations
        for perm in permutations(v2[:n]):
            all_distinct.append(perm)
            if len(all_distinct) >= 6:
                break
    # Compound positions
    compound_tuples = []
    if n >= 2 and v2:
        a = v2[0]
        for pos in range(n):
            tup = [a] * n
            tup[pos] = f"({a} ◇ {a})"
            compound_tuples.append(tuple(tup))

    all_tuples = (diagonal_tuples + perturbation_tuples + all_distinct + compound_tuples)
    # Dedup
    seen_t, unique_tuples = set(), []
    for t in all_tuples:
        ts = " ".join(t)
        if ts not in seen_t:
            seen_t.add(ts)
            unique_tuples.append(t)
    unique_tuples = unique_tuples[:max_haves * 2]

    cands: list[str] = []
    closers = ["grind", "aesop", "simp_all"]

    # Single-have (already covered by tactic_sweep but include for completeness)
    if n > 0 and v2:
        for t in unique_tuples[:6]:
            args = " ".join(t)
            for closer in closers:
                cands.append(f"{intro}\nhave k := h {args}\n{closer}")

    # Pairs
    for i, t1 in enumerate(unique_tuples[:6]):
        for j, t2 in enumerate(unique_tuples[:6]):
            if i == j:
                continue
            a1 = " ".join(t1); a2 = " ".join(t2)
            cands.append(
                f"{intro}\nhave k1 := h {a1}\nhave k2 := h {a2}\ngrind"
            )

    # Triples — focus on diagonals + one perturbation
    for d in diagonal_tuples[:3]:
        for p in perturbation_tuples[:3]:
            ad = " ".join(d); ap = " ".join(p)
            for d2 in diagonal_tuples[:2]:
                if d == d2:
                    continue
                ad2 = " ".join(d2)
                cands.append(
                    f"{intro}\nhave k1 := h {ad}\nhave k2 := h {ap}\nhave k3 := h {ad2}\ngrind"
                )

    # Massive: 5 haves with diagonal + perturbations
    if len(unique_tuples) >= 5 and v2:
        sel = unique_tuples[:5]
        haves = "\n".join(f"have k{i+1} := h {' '.join(t)}" for i, t in enumerate(sel))
        cands.append(f"{intro}\n{haves}\ngrind")
        cands.append(f"{intro}\n{haves}\naesop")
        # With symm versions
        haves_with_symm = haves + "\n" + "\n".join(f"have k{i+1}s := (h {' '.join(t)}).symm" for i, t in enumerate(sel[:3]))
        cands.append(f"{intro}\n{haves_with_symm}\ngrind")

    # Dedup
    seen, uniq = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def superposition_sweep(eq1: str, eq2: str, judge_call: Callable[[str], dict],
                         max_attempts: int = 40) -> bool:
    """Try superposition-style proofs (heavy h-instantiation + grind)."""
    candidates = build_superposition_candidates(eq1, eq2)
    for proof in candidates[:max_attempts]:
        result = judge_call(lean_true(proof))
        if result.get("status") == "accepted":
            return True
    return False


def meta_closure_sweep(eq1_id: int, eq2_id: int, eq1: str, eq2: str,
                        adj: dict, eqdefs: dict,
                        judge_call: Callable[[str], dict],
                        max_aux_attempts: int = 12) -> bool:
    """Try meta-closure auxiliary lemma proofs.

    For each candidate auxiliary equation E_aux:
      1. Build the closure chain h → E_aux as inlined Lean.
      2. Promote that to a typed lemma `eq_aux : ∀ vars, body`.
      3. Try `intro vars; nth_rewrite N [±eq_aux]; apply h` for various N, ±, and
         apply variants.
    """
    global _eqdefs_cache
    _eqdefs_cache = eqdefs  # used by _aux_chain_proof for tactic-step annotations
    v2 = variables_of(eq2)
    intro_v2 = "intro " + " ".join(v2) if v2 else ""

    # Order candidate aux equations: shape-simple priority list first, then any
    # node with out-edges into "simple territory" (rough heuristic).
    candidates_aux = list(_SIMPLE_AUX_PRIORITY)
    # Add any aux that's reachable AND has very small variable count
    reachable = set()
    if eq1_id in adj:
        import collections as _c
        seen = {eq1_id}
        q = _c.deque([eq1_id])
        while q:
            u = q.popleft()
            for entry in adj.get(u, ()):
                v = entry[0]
                if v not in seen:
                    seen.add(v); q.append(v); reachable.add(v)
    # Sort the rest by number of vars (fewer = simpler)
    extra = sorted(
        [a for a in reachable if a not in candidates_aux],
        key=lambda a: len(eqdefs.get(a, ("xx", ""))[0].split())
    )
    candidates_aux = [a for a in candidates_aux if a in reachable] + extra[:max_aux_attempts]

    attempted = 0
    for aux_id in candidates_aux:
        if attempted >= max_aux_attempts:
            break
        ed = eqdefs.get(aux_id)
        if not ed:
            continue
        chain = _aux_chain_proof(adj, eq1_id, aux_id)
        if chain is None:
            continue
        attempted += 1

        aux_vars, aux_body = ed
        # Build the proof template. After the chain, `h` refers to E_aux.
        # We rename it to `eq_aux` for clarity.
        for direction in ["", "← "]:
            for occ in [1, 2, 3]:
                for closer in ["apply h", "grind", "first | apply h | grind"]:
                    proof = f"""
have eq_aux : ∀ ({aux_vars} : G), {aux_body} := by
    {chain}
    exact h
{intro_v2}
nth_rewrite {occ} [{direction}eq_aux]
{closer}
""".strip()
                    result = judge_call(lean_true(proof))
                    if result.get("status") == "accepted":
                        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Layer 5 — LLM fallback (single-prompt MULTI + DIAGNOSE feedback loop)
# ─────────────────────────────────────────────────────────────────────────────
#
# Reads OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL from env (loaded
# from .env by the runner).  Uses OpenAI-compatible chat completions API.
#
# Strategy:
#   Round 1: MULTI — ask for 3 differentiated proof candidates
#   Round 2+: DIAGNOSE — feed back judge stderr, ask for minimal fix
#
# Stops on: any candidate accepted, budget exhausted, or 5 rounds elapsed.

import json as _json
import os as _os
import urllib.request as _urlreq

_LLM_PROMPT_MULTI = """You are solving a magma equational theory problem in Lean 4.

Hypothesis (h): ∀ vars, {eq1}
Goal:           ∀ vars, {eq2}

Possible verdicts: TRUE (write proof) or FALSE (write counterexample table on Fin n).

Available tactics: simp, simp_all, grind, aesop, decide, omega, rfl, rw, calc.
Allowed lemma prefixes: Mathlib.*, Eq.*, Magma.*, Std.*, congr_arg, congrArg.

Provide 3 differentiated attempts in a single response:
  Attempt A: most direct — try simple `intro x y z; grind` style or short rewrite chain.
  Attempt B: alternative — different verdict, OR different tactic family.
  Attempt C: defensive — assume the easy paths failed, try a more elaborate construction.

Strict JSON output, no markdown, no commentary:
{{"attempts": [
  {{"verdict": "true", "proof": "<tactic body, no `def submission`, no imports>"}},
  {{"verdict": "true", "proof": "..."}},
  {{"verdict": "false", "counterexample_table": [[0,1],[1,0]]}}
]}}
"""

_LLM_PROMPT_DIAGNOSE = """Your last submission was rejected.  Read the Lean error and propose ONE fixed proof.

Hypothesis: ∀ vars, {eq1}
Goal:       ∀ vars, {eq2}

Last attempt (verdict={last_verdict}):
{last_proof}

Lean error:
{last_error}

Reply STRICT JSON, no markdown:
{{"verdict": "true|false", "proof": "..." OR "counterexample_table": [[...]]}}
"""


def llm_call(messages: list[dict], timeout: int = 180,
             max_tokens: int = 1500) -> str:
    """POST to OpenAI-compatible /chat/completions, return assistant content.

    SiliconFlow's DeepSeek-V4-Flash takes ~10-30s for 1500-token completions;
    timeout=180 gives 6× headroom. max_tokens trimmed from 4096 to keep
    response time bounded — proof bodies are short.
    """
    api_key = _os.environ.get("OPENAI_API_KEY", "").strip()
    base_url = _os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/").rstrip("/")
    model = _os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        return ""
    body = _json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = _urlreq.Request(
        base_url + "/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except Exception:
        return ""


def _extract_json(text: str) -> dict | None:
    """Pull JSON from possibly-fenced LLM output."""
    if not text:
        return None
    text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    try:
        return _json.loads(text.strip())
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return _json.loads(m.group())
        except Exception:
            pass
    return None


def _llm_attempt_to_lean(attempt: dict) -> tuple[str, str] | None:
    """Convert an LLM attempt dict to (verdict, lean_code). Returns None if malformed."""
    verdict = attempt.get("verdict", "").lower()
    if verdict == "true":
        proof = attempt.get("proof", "").strip()
        if not proof:
            return None
        # Strip wrappers LLMs sometimes add
        if ":= by" in proof:
            proof = re.sub(r"^.*?:=\s*by\s*\n?", "", proof, count=1, flags=re.DOTALL)
        proof = re.sub(r"^\s*by\s+", "", proof)
        proof = re.sub(r"^\s*import\s+.*\n?", "", proof, flags=re.MULTILINE)
        proof = proof.strip()
        return verdict, lean_true(proof)
    elif verdict == "false":
        tbl = attempt.get("counterexample_table")
        if not tbl or not isinstance(tbl, list):
            return None
        return verdict, _make_false_code(len(tbl), tbl)
    return None


def _make_false_code(n: int, table: list[list[int]]) -> str:
    """Same shape as solvers/stellar_v1.make_false_code (Fin n with op table)."""
    table_str = _json.dumps(table)
    return (
        "import JudgeProblem\n"
        "import JudgeDecide.DecideBang\n"
        "import JudgeFinOp.MemoFinOp\n"
        "open MemoFinOp\n\n"
        "def submission : Goal := by\n"
        f"  let m : Magma (Fin {n}) := {{\n"
        f"    op := finOpTable \"{table_str}\"\n"
        f"  }}\n"
        f"  refine ⟨Fin {n}, m, ?_⟩\n"
        f"  decideFin!\n"
    )


def llm_solve(eq1: str, eq2: str,
              judge_true: Callable[[str], dict],
              judge_false: Callable[[str], dict],
              max_rounds: int = 4) -> bool:
    """Try the LLM (MULTI then DIAGNOSE feedback loop) up to max_rounds.
    Returns True on accept.
    """
    if not _os.environ.get("OPENAI_API_KEY", "").strip():
        return False

    # Round 1: MULTI — ask for 3 candidates
    prompt = _LLM_PROMPT_MULTI.format(eq1=eq1, eq2=eq2)
    response = llm_call([{"role": "user", "content": prompt}], timeout=120)
    parsed = _extract_json(response)
    if parsed is None:
        return False
    attempts = parsed.get("attempts", [])
    if not isinstance(attempts, list):
        attempts = [parsed]  # tolerate single-attempt response

    last_error = None
    last_proof = None
    last_verdict = None
    for attempt in attempts[:3]:
        ka = _llm_attempt_to_lean(attempt)
        if ka is None:
            continue
        verdict, code = ka
        result = (judge_true if verdict == "true" else judge_false)(code)
        if result.get("status") == "accepted":
            return True
        last_error = (result.get("stderr") or result.get("message") or "")[:1500]
        last_proof = attempt.get("proof") or _json.dumps(attempt.get("counterexample_table", ""))
        last_verdict = verdict

    # Rounds 2+: DIAGNOSE feedback loop
    for _ in range(max_rounds - 1):
        if last_error is None:
            break
        prompt = _LLM_PROMPT_DIAGNOSE.format(
            eq1=eq1, eq2=eq2,
            last_verdict=last_verdict, last_proof=last_proof, last_error=last_error,
        )
        response = llm_call([{"role": "user", "content": prompt}], timeout=120)
        parsed = _extract_json(response)
        if parsed is None:
            break
        ka = _llm_attempt_to_lean(parsed)
        if ka is None:
            break
        verdict, code = ka
        result = (judge_true if verdict == "true" else judge_false)(code)
        if result.get("status") == "accepted":
            return True
        last_error = (result.get("stderr") or result.get("message") or "")[:1500]
        last_proof = parsed.get("proof") or _json.dumps(parsed.get("counterexample_table", ""))
        last_verdict = verdict

    return False


