module

public import VersoSlides

open VersoSlides

#doc (Slides) "Signal Shot: project update" =>

# Signal Shot: project update

%%%
backgroundColor := some "#1f2937"
%%%

Stanford, 7th November 2026

{image "images/BAIF_Logo.png" (height := "60px")}[Beneficial AI Foundation logo]

# Signal Shot

* Machine-checked proof that Signal's cryptography does what it claims
* Target: libsignal, about 45,000 lines of Rust plus its cryptographic dependencies
* Launched April 2026: BAIF with the Lean FRO and Signal engineers
* Open source messaging software, open source tools for verification

# The gap

* Protocol designs are proved secure in one tool, code is checked in another
* Nothing formally connects them: code can drift from design unnoticed
* Proofs have needed scarce experts, so coverage is thin

# End-to-end in one tool

* Rust → (Aeneas) → Lean
* Functional correctness: no panic and the code matches its spec
* Protocol security: confidentiality and authenticity against defined attackers
* The link: the code implements the protocol proved secure
* Proofs live with the code, so engineers can update them as it evolves

# Where things stand

(Let's have an image of the entire project showing approximate progress)

## Functional correctness

* curve25519-dalek: proofs complete
* Post-quantum code (SPQR): nearing completion
* Core libsignal: in progress

## Protocol security

* PQXDH (this is what Galois did?): complete, integration in progress
* (What is Sergiu working on?): nearing completion, integration to proceed soon
* (What is Christiano working on?): nearing completion

No problems found!

# Proofs in the hands of the engineers and protocol designers

* Proof repair?
* Updates?
* Proximity of specs to Rust code?

# AI

Yep, AI is very good at writing high quality Lean code, allows us to move fast

# Organization of large Lean repos

TODO: image of the breakdown of lines of code in the curve25519-dalek project, illustration of how recall and print axioms can be used

# Sophisticated specs: e.g., eliiptic curves

TODO: `mul` and `is_small_order` specs

Lean allows essentially unlimited expressiveness in the specs

# Aeneas translation

* Tool in active development and we are proud to support it
* Minimal inconvenience, dealing with coverage problems using patches
* Aeneas expanding coverage very soon (direct question to Son Ho in audience)

# Protocol security

TODO: PQXDH security statement or something like this?

# Large numbers: hide them

TODO

# Performance

{image "images/spqr-performance.png" (height := "440px")}[SPQR build performance over the last 200 commits]

:::class "caption"
SPQR, last 200 commits. Left: build and rebuild time (s). Right: peak RAM.
:::

:::notes
Specs and proofs kept growing. The drops come from Lean updates and refactoring: the same statements, proved more efficiently.
:::

# Summary

* End-to-end: Rust code to protocol security, all in Lean
* Next: proofs in the engineers' hands, run on every change
* TODO: links
