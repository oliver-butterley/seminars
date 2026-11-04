"""Generate the functional-correctness scope diagram (Rust crates only).

Sizes (shown as numbers): non-blank, non-comment lines of Rust in each crate's src/ (tests, benches,
examples excluded), at the versions pinned by libsignal e8cc2dd (libsignal-verify).
Dependencies: `cargo metadata` normal deps of libsignal-protocol, libsignal-core,
signal-crypto and spqr.
"""
import json, sys

g = json.load(open(sys.argv[1]))
out = sys.argv[2]
L = lambda n: g[n]["code"]

def k(x):
    return f"{x/1000:.1f}k"

libcrux = ["libcrux-ml-kem", "libcrux-hacl-rs", "libcrux-sha3", "libcrux-intrinsics",
           "libcrux-traits", "libcrux-sha2", "libcrux-secrets", "libcrux-hmac",
           "libcrux-platform", "libcrux-macros"]
curve = ["curve25519-dalek", "x25519-dalek", "curve25519-dalek-derive"]
rustcrypto = ["aes", "sha2", "digest", "cipher", "polyval", "sha1", "ctr", "crypto-common",
              "block-buffer", "cbc", "hmac", "aes-gcm-siv", "hkdf", "universal-hash", "ghash"]
hpke = ["hpke-rs", "hpke-rs-crypto"]
sig = ["libsignal-protocol", "spqr", "libsignal-core", "signal-crypto"]
tot = lambda xs: sum(L(x) for x in xs)
T = {"libcrux": tot(libcrux), "curve": tot(curve), "rc": tot(rustcrypto), "hpke": tot(hpke)}
grand = sum(T.values()) + tot(sig)

# colours (white text on all fills, contrast >= 4.5)
C = {"sig": "#2b4c7e", "libcrux": "#6b3fa0", "curve": "#7a5520", "rc": "#1f6f54",
     "hpke": "#22686a"}
INK, MUTED, EDGE = "#1e293b", "#64748b", "#475569"
FONT = "'Source Sans Pro','Source Sans 3','Helvetica Neue',Helvetica,Arial,sans-serif"

W, H = 960, 460
s = []
add = s.append
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
    f'font-family="{FONT}">')
add('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{EDGE}"/></marker></defs>')
BG = f'<rect width="{W}" height="{H}" fill="#ffffff"/>'
add(BG)

def box(x, y, w, h, fill, title, size, sub=(), dy=0):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}"/>')
    add(f'<text x="{x+12}" y="{y+24+dy}" fill="#fff" font-size="15.5" font-weight="600">{title}</text>')
    add(f'<text x="{x+w-12}" y="{y+24+dy}" fill="#fff" font-size="14" text-anchor="end" '
        f'opacity="0.9">{k(size)}</text>')
    for i, line in enumerate(sub):
        add(f'<text x="{x+12}" y="{y+46+dy+i*17}" fill="#fff" font-size="12.5" opacity="0.88">{line}</text>')

def line(pts, behind=False):
    d = " ".join(f"{'M' if i == 0 else 'L'}{x},{y}" for i, (x, y) in enumerate(pts))
    el = (f'<path d="{d}" fill="none" stroke="{EDGE}" stroke-width="1.6" '
          'stroke-linejoin="round" marker-end="url(#ah)"/>')
    if behind:
        s.insert(s.index(BG) + 1, el)
    else:
        add(el)

def label(x, y, text):
    add(f'<text x="{x}" y="{y}" fill="{MUTED}" font-size="12">{text}</text>')

# ── Grid: every box the same width; one height per row ──
CW, GAP = 212, 24
X = [20 + i * (CW + GAP) for i in range(4)]     # 20, 256, 492, 728
CX = [x + CW / 2 for x in X]

# Row 1: libsignal crates
y1, h1 = 64, 84
add(f'<text x="20" y="{y1-16}" fill="{MUTED}" font-size="12" font-weight="600" '
    'letter-spacing="0.08em">LIBSIGNAL</text>')
row1 = [("spqr", "Sparse Post-Quantum Ratchet"),
        ("libsignal-protocol", "PQXDH, Double/Triple Ratchet"),
        ("signal-crypto", "AES modes, hashes, HPKE"),
        ("libsignal-core", "Curve25519 keys, addresses")]
for i, (n, sub) in enumerate(row1):
    box(X[i], y1, CW, h1, C["sig"], n, L(n), [sub], dy=(h1 - 64) / 2)

mid1 = y1 + h1 / 2
line([(X[1], mid1), (X[0] + CW + 2, mid1)])            # protocol -> spqr
line([(X[1] + CW, mid1), (X[2] - 2, mid1)])            # protocol -> signal-crypto
line([(X[2] + CW, mid1), (X[3] - 2, mid1)])            # signal-crypto -> core
line([(CX[1], mid1 + 18), (X[3] - 2, mid1 + 18)], behind=True)  # protocol -> core, behind

# Row 2: RustCrypto, libcrux, hpke-rs, curve25519
y2, h2 = 224, 160
b1 = y1 + h1
traits = tot(['digest', 'cipher', 'universal-hash', 'crypto-common', 'block-buffer'])
box(X[0], y2, CW, h2, C["rc"], "RustCrypto", T["rc"], [
    "15 crates · used by all four",
    f"aes {k(L('aes'))} · aes-gcm-siv {k(L('aes-gcm-siv'))}",
    f"ctr {k(L('ctr'))} · cbc {k(L('cbc'))}",
    f"ghash + polyval {k(L('ghash') + L('polyval'))}",
    f"sha2 {k(L('sha2'))} · sha1 {k(L('sha1'))}",
    f"hmac {k(L('hmac'))} · hkdf {k(L('hkdf'))}",
    f"traits {k(traits)}"])
box(X[1], y2, CW, h2, C["libcrux"], "libcrux", T["libcrux"], [
    "10 crates (Cryspen)",
    f"ml-kem {k(L('libcrux-ml-kem'))}",
    f"hacl-rs (SHA-2, HMAC) {k(L('libcrux-hacl-rs'))}",
    f"sha3 {k(L('libcrux-sha3'))} · intrinsics {k(L('libcrux-intrinsics'))}",
    f"traits {k(L('libcrux-traits'))} · secrets {k(L('libcrux-secrets'))}",
    f"4 smaller crates {k(tot(['libcrux-sha2','libcrux-hmac','libcrux-platform','libcrux-macros']))}"])
box(X[2], y2, CW, h2, C["hpke"], "hpke-rs", T["hpke"], [
    "2 crates",
    f"hpke-rs {k(L('hpke-rs'))}",
    f"hpke-rs-crypto {k(L('hpke-rs-crypto'))}"])
box(X[3], y2, CW, h2, C["curve"], "curve25519", T["curve"], [
    "3 crates",
    f"curve25519-dalek {k(L('curve25519-dalek'))}",
    f"x25519-dalek {k(L('x25519-dalek'))}",
    f"dalek-derive {k(L('curve25519-dalek-derive'))}"])

bus = (b1 + y2) / 2
line([(CX[0], b1), (CX[0], bus), (X[1] + 50, bus), (X[1] + 50, y2 - 2)])  # spqr -> libcrux
label(CX[0] + 8, bus - 7, "ML-KEM, HMAC")
line([(CX[1] + 30, b1), (CX[1] + 30, y2 - 2)])                            # protocol -> libcrux
label(CX[1] + 38, bus + 4, "ML-KEM")
line([(CX[2], b1), (CX[2], y2 - 2)])                                      # signal-crypto -> hpke-rs
label(CX[2] + 8, bus + 4, "HPKE")
line([(CX[3], b1), (CX[3], y2 - 2)])                                      # core -> curve25519
label(CX[3] + 8, bus + 4, "X25519, XEdDSA")
ya = y2 + 60
line([(X[2], ya), (X[1] + CW + 2, ya)])                                   # hpke-rs -> libcrux (SHA-3)

# Footer
add(f'<text x="20" y="{y2+h2+30}" fill="{MUTED}" font-size="12.5">'
    'hpke-rs uses libcrux for SHA-3; curve25519-dalek uses RustCrypto digest. '
    'Also throughout: subtle (constant-time), zeroize.</text>')
add(f'<text x="20" y="{y2+h2+50}" fill="{MUTED}" font-size="12.5">'
    'Lines of Rust: non-blank, non-comment, src/ only, tests excluded. '
    'A → B: A depends on B.</text>')
add('</svg>')
open(out, "w").write("\n".join(s))
print("grand", grand, T)
