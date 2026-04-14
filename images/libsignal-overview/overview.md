# Functional Correctness Scope — Crate Overview

| Crate | Lines | Category |
|---|---|---|
| `libsignal-protocol` | ~10,900 | **libsignal** |
| `spqr` | ~8,800 | **libsignal** |
| `libsignal-core` | ~1,800 | **libsignal** |
| `signal-crypto` | ~880 | **libsignal** |
| | **~22,400** | |
| `libcrux` (8 crates) | ~44,600 | **libcrux** |
| | **~44,600** | |
| `curve25519-dalek` | ~33,000 | **curve-dalek** |
| `x25519-dalek` | ~680 | **curve-dalek** |
| | **~33,700** | |
| `aes` | ~6,650 | **RustCrypto** |
| `sha2` | ~2,400 | **RustCrypto** |
| `hpke-rs` | ~2,200 | **other** |
| `aes-gcm-siv` | ~830 | **RustCrypto** |
| | **~12,100** | |

**Grand total: ~113k lines** — libcrux is the biggest chunk (40%), then curve-dalek (30%), libsignal (20%), others (10%).
