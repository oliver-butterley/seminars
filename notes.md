
# Title: Verify Libsignal in Lean

(add footnote for Verify with explanations: Verify in the sense of: - Proofs live side-by-side with the code, called in CI, - full end-to-end, functional verification to security proofs of the protocols) 

## 4 large boxes at the top:

Level 0 — PQXDH Computational Proof

A Lean theorem that PQXDH achieves its security definition (from the paper), proof obligations that ultimately reduce to the hardness of ML-KEM and the CDH assumption.

Level 1 — Double Ratchet Computational Proof

Formalise in Lean the security theorem of Cohn-Gordon et al. 2019.

Level 2 — SPQR/Triple Ratchet Proof

Formalise the SPQR security proof from the EuroCrypt/USENIX papers, building on the ratchet infrastructure from Level 1.

Level 4 — Protocol Composition

Lean proof that PQXDH initialization composed with the Triple Ratchet achieves end-to-end security for a conversation: if a conversation is initiated via PQXDH and subsequent messages use Triple Ratchet, then the following security properties hold for the full session.

## Below that, a row of boxes: "abstract Cryptographic Infrastructure"

KEM - Key encapsulation mechanism
DH - Diffie–Hellman key exchange
AEAD - authenticated encryption with associated data 
KDF - Key derivation function

(the last ones should be distiguished as security games)
IND-CCA2 - Indistinguishability under Adaptive Chosen-Ciphertext Attack
PRF 
etc.

## Further down, a row of three boxes which represent Rust crates

for each crate highlight the entry-point functions at the top of the box

below that, display the idea of many crates, variously depending on others, each with the entry point functions suggested by a different part at the top of the box.


## Tasks

- Refine the list of abstract models/interfaces
- Create each abstract interfaces
- Identify the libsignal entry point functions
- Write specs for each entry point function
- Determine all dependency crates & entry point functions for each crate
- Use Aeneas to extract each crate to Lean
- Establish a standard structure and utils for repos (building on the lessons we have learnt with lean-dalek) verifying rust crates.
- Prove functional correctness for each crate