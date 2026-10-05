"""Gradient descent variants on an ill-conditioned least-squares problem (numpy only).

usage: run.py --system gd|momentum|adam --task cond10|cond1000 --seed S --out metrics.json [--beta 0.9]
Writes {"final_loss": float, "steps_to_tol": float}.
"""
import argparse, json
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--system", required=True); ap.add_argument("--task", required=True)
ap.add_argument("--seed", type=int, required=True); ap.add_argument("--out", required=True)
ap.add_argument("--beta", type=float, default=0.9); ap.add_argument("--steps", type=int, default=400)
a = ap.parse_args()

rng = np.random.default_rng(a.seed)
d, n = 20, 200
cond = {"cond10": 10.0, "cond1000": 1000.0}[a.task]
scales = np.geomspace(1.0, np.sqrt(cond), d)            # column scales set the condition number
X = rng.normal(size=(n, d)) * scales
w_true = rng.normal(size=d)
y = X @ w_true + 0.01 * rng.normal(size=n)
H = X.T @ X / n
L = float(np.linalg.eigvalsh(H).max())                  # smoothness constant

def loss(w):
    r = X @ w - y
    return float(r @ r) / (2 * n)

w_star = np.linalg.lstsq(X, y, rcond=None)[0]
f_star = loss(w_star)
w = np.zeros(d); v = np.zeros(d); m = np.zeros(d); s = np.zeros(d)
tol, hit = 1e-3, None
for t in range(1, a.steps + 1):
    g = X.T @ (X @ w - y) / n
    if a.system == "gd":
        w = w - (1.0 / L) * g
    elif a.system == "momentum":                        # heavy ball
        v = a.beta * v - (1.0 / L) * g
        w = w + v
    elif a.system == "adam":
        m = 0.9 * m + 0.1 * g; s = 0.999 * s + 0.001 * g * g
        w = w - 0.05 * (m / (1 - 0.9 ** t)) / (np.sqrt(s / (1 - 0.999 ** t)) + 1e-8)
    else:
        raise SystemExit(f"unknown system {a.system}")
    if hit is None and loss(w) - f_star < tol:
        hit = t
json.dump({"final_loss": loss(w) - f_star, "steps_to_tol": float(hit if hit is not None else a.steps)}, open(a.out, "w"))
