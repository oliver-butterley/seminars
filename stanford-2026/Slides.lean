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
* Target: libsignal and its cryptographic dependencies
* Launched April 2026: BAIF with the Lean FRO and Signal engineers
* Open source messaging software, open source tools for verification

# The target: libsignal and its cryptography

{image "images/libsignal-overview/functional-correctness.svg" (width := "100%")}[libsignal crates and their cryptographic dependencies, with sizes]

# Building on great work by others

## Protocol design

* PQXDH analysed in ProVerif and CryptoVerif, with design improvements (Bhargavan, Jacomme, Kiefer, Schmidt)
* SPQR: security proofs (Eurocrypt and USENIX 2025), ProVerif models by Signal and Cryspen

## Code

* Cryspen's hax → F\*: panic freedom and core correctness of SPQR
* libcrux ML-KEM: panic freedom, functional correctness, secret independence
* Signal in-house: proofs run on every push, and the build fails if they fail

:::class "caption"
[USENIX Security 2024](https://www.usenix.org/conference/usenixsecurity24/presentation/bhargavan) · [Signal: SPQR](https://signal.org/blog/spqr/) · [Cryspen: SPQR verification](https://cryspen.com/post/signal-spqr-verification/)
:::

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

{image "images/dalek-composition/dalek-composition.svg" (width := "100%")}[curve25519-dalek verification in lines: Rust, generated Lean, spec statements, definitions and proofs]

# Spec summaries: recall and print axioms

TODO: illustration of how recall and print axioms can be used

# Sophisticated specs: e.g., eliiptic curves

TODO: `mul` and `is_small_order` specs

Lean allows essentially unlimited expressiveness in the specs

# Rust → Lean with Aeneas

:::hstack
```code rust
pub(crate) fn mul_by_pow_2(&self, k: u32)
    -> EdwardsPoint {
  debug_assert!(k > 0);
  let mut r: CompletedPoint;
  let mut s = self.as_projective();
  let mut i = 0;
  while i < k - 1 {
    r = s.double();
    s = r.as_projective();
    i += 1;
  }
  s.double().as_extended()
}
```

```code lean
def mul_by_pow_2_loop (k : U32)
    (s : ProjectivePoint) (i : U32) :
    Result ProjectivePoint := do
  let i1 ← k - 1#u32
  if i < i1 then
    let r ← ProjectivePoint.double s
    let s1 ← CompletedPoint.as_projective r
    let i2 ← i + 1#u32
    mul_by_pow_2_loop k s1 i2
  else ok s
partial_fixpoint

def mul_by_pow_2 (self : EdwardsPoint)
    (k : U32) : Result EdwardsPoint := do
  massert (k > 0#u32)
  let s ← EdwardsPoint.as_projective self
  let s1 ← mul_by_pow_2_loop k s 0#u32
  let cp ← ProjectivePoint.double s1
  CompletedPoint.as_extended cp
```
:::

:::class "caption"
`curve25519-dalek/src/edwards.rs` and its Aeneas translation in `Funs.lean` (namespaces shortened). Every operation returns a `Result`: `k - 1` and `i + 1` are checked for overflow, the loop becomes a recursive function.
:::

# Aeneas translation

* Tool in active development and we are proud to support it
* Minimal inconvenience, dealing with coverage problems using patches
* Aeneas expanding coverage very soon (direct question to Son Ho in audience)

:::class "caption"
[aeneasverif.github.io](https://aeneasverif.github.io/)
:::

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

:::class "key-box"
Signal Shot: [beneficialaifoundation.org/blog/signal-shot](https://www.beneficialaifoundation.org/blog/signal-shot)

Lean: [lean-lang.org](https://lean-lang.org/)

Aeneas: [aeneasverif.github.io](https://aeneasverif.github.io/)
:::
