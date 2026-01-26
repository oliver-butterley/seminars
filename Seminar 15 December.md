# Verifying curve25519-dalek using Lean 

Oliver Butterley 

The Beneficial AI Foundation & University of Rome Tor Vergata

[BAIF logo]

Lean@Google, 15 December 2025

## Overview

What is the project: 
- Functional verification of the Rust crate curve25519-dalek using Aeneas and Lean
Motives: 
- Part of the goal of verifying libsignal + dependencies
- Scaling verification (easier, cheaper and commonplace)

[Picture of the team (github)]

Zero fidelity: we choose Rust to Lean via Aeneas because it is the most relevant combination today

Repo link: https://github.com/Beneficial-AI-Foundation/curve25519-dalek-lean-verify

## What is curve25519-dalek?

- Rust crate of open source cryptographic primitives
- Structures to describe points on the elliptic curve, scalars, functions for manipulating them fast 
- ~200 functions

[show dependency graph and progress plot]

## A few example functions

### `reduce`

```rust
pub struct FieldElement51(pub(crate) [u64; 5]);
```

```rust
/// Given 64-bit input limbs, reduce to enforce the bound 2^(51 + epsilon).
fn reduce(mut limbs: [u64; 5]) -> FieldElement51 {
    const LOW_51_BIT_MASK: u64 = (1u64 << 51) - 1;

    // Since the input limbs are bounded by 2^64, the biggest
    // carry-out is bounded by 2^13.
    //
    // The biggest carry-in is c4 * 19, resulting in
    //
    // 2^51 + 19*2^13 < 2^51.0000000001
    //
    // Because we don't need to canonicalize, only to reduce the
    // limb sizes, it's OK to do a "weak reduction", where we
    // compute the carry-outs in parallel.

    let c0 = limbs[0] >> 51;
    let c1 = limbs[1] >> 51;
    let c2 = limbs[2] >> 51;
    let c3 = limbs[3] >> 51;
    let c4 = limbs[4] >> 51;

    limbs[0] &= LOW_51_BIT_MASK;
    limbs[1] &= LOW_51_BIT_MASK;
    limbs[2] &= LOW_51_BIT_MASK;
    limbs[3] &= LOW_51_BIT_MASK;
    limbs[4] &= LOW_51_BIT_MASK;

    limbs[0] += c4 * 19;
    limbs[1] += c0;
    limbs[2] += c1;
    limbs[3] += c2;
    limbs[4] += c3;

    FieldElement51(limbs)
}
```

- Quick algorithms for manipulations mod `2 ^ 255 - 19`.
- Field element represented by 5 limbs, `∑ i ∈ range 5, 2 ^ (51 * i) * limbs[i]`.

### `negate`

```rust
/// Invert the sign of this field element
pub fn negate(&mut self) {
    // See commentary in the Sub impl
    let neg = FieldElement51::reduce([
        36028797018963664u64 - self.0[0],
        36028797018963952u64 - self.0[1],
        36028797018963952u64 - self.0[2],
        36028797018963952u64 - self.0[3],
        36028797018963952u64 - self.0[4],
    ]);
    self.0 = neg.0;
}
```

### `double`

```rust
pub struct ProjectivePoint {
    pub X: FieldElement51,
    pub Y: FieldElement51,
    pub Z: FieldElement51,
}
```

```rust
pub struct CompletedPoint {
    pub X: FieldElement51,
    pub Y: FieldElement51,
    pub Z: FieldElement51,
    pub T: FieldElement51,
}
```

```rust
impl ProjectivePoint {
    /// Double this point: return self + self
    pub fn double(&self) -> CompletedPoint {
        // Double()
        let XX = self.X.square();
        let YY = self.Y.square();
        let ZZ2 = self.Z.square2();
        let X_plus_Y = &self.X + &self.Y;
        let X_plus_Y_sq = X_plus_Y.square();
        let YY_plus_XX = &YY + &XX;
        let YY_minus_XX = &YY - &XX;

        CompletedPoint {
            X: &X_plus_Y_sq - &YY_plus_XX,
            Y: YY_plus_XX,
            Z: YY_minus_XX,
            T: &ZZ2 - &YY_minus_XX,
        }
    }
}
```

Structures to conveniently encode a point on the elliptic curve, library designed so that coordinates are always valid.

### `add` (Scalar52)

```rust
pub struct Scalar52(pub [u64; 5]);
```

```rust
    /// Compute `a + b` (mod l)
    pub fn add(a: &Scalar52, b: &Scalar52) -> Scalar52 {
        let mut sum = Scalar52::ZERO;
        let mask = (1u64 << 52) - 1;

        // a + b
        let mut carry: u64 = 0;
        let mut i = 0;
        while i < 5 {
            carry = a[i] + b[i] + (carry >> 52);
            sum[i] = carry & mask;
            i += 1;
        }

        // subtract l if the sum is >= l
        Scalar52::sub(&sum, &constants::L)
    }
```
Subtle differences in each part of the code.

## Workflow

- Choose a set of functions of interest (1)
- Choose a subset of the functions of interest (2)
- Modify Rust source if required (3)
- Extract the functions to Lean using Aeneas (1)
- Apply tweaks to the extracted Lean (4)
- Add definitions / spec theorems for external functions (5)
- Add spec theroem statements for every functions (1)
- Add a proof for each spec theorem (1)

[Initially show list with only the items marked (1), then add the other items as numbered, then add a loop fromt he last item back to the previous one]

## Lightweight tooling

- Work in a repo with extensive CI

- Extraction related files
    - `extract-functions.txt`
    - `src-modifications.diff`
    - `aeneas-tweaks.txt`

- CI
    - check Rust code (compile, test, fmt)
    - check Lean code
    - build project site
    - count number specified and verified
    - confirm Aeneas extracted code hasn't been modified
    - confirm no additional modifications to Rust source

[Insert status page image]

## Example function: `reduce`

```lean
/-- Curve25519 is the elliptic curve over the prime field with order p -/
def p : Nat := 2^255 - 19

/-- Interpret a Field51 (five u64 limbs used to represent 51 bits each) as a natural number -/
def Field51_as_Nat (limbs : Array U64 5#usize) : Nat :=
  ∑ i ∈ Finset.range 5, 2 ^ (51 * i) * limbs[i]!.val
```

```lean
/-- **Spec and proof concerning `backend.serial.u64.field.FieldElement51.reduce`**:
- Does not overflow
- All the limbs of the result are small, ≤ 2^(51 + ε)
- The result is equal to the input mod p. -/
@[progress]
theorem reduce_spec (limbs : Array U64 5#usize) :
    ∃ result, reduce limbs = ok result ∧
    (∀ i < 5, result[i]!.val ≤ 2^51 + (2^13 - 1) * 19) ∧
    Field51_as_Nat limbs ≡ Field51_as_Nat result [MOD p] := by
  unfold reduce
  progress*
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · constructor
    · intro i _
      interval_cases i
      all_goals simp [*]; scalar_tac
    · simp [Field51_as_Nat, Finset.sum_range_succ, p, Nat.ModEq, *]; omega
```

## Example function: `negate`

```lean
/-- **Spec and proof concerning `backend.serial.u64.field.FieldElement51.negate`**:
- The result r_inv represents the additive inverse of the input r in 𝔽_p, i.e.,
  Field51_as_Nat(r) + Field51_as_Nat(r_inv) ≡ 0 (mod p)
- All the limbs of the result are small, ≤ 2^(51 + ε)
- Requires that input limbs of r are bounded to avoid underflow:
  - Limb 0 must be ≤ 36028797018963664
  - Limbs 1-4 must be ≤ 36028797018963952 -/
@[progress]
theorem negate_spec (r : FieldElement51) (h : ∀ i < 5, r[i]!.val < 2 ^ 54) :
    ∃ r_inv, negate r = ok r_inv ∧
    (Field51_as_Nat r + Field51_as_Nat r_inv) % p = 0 ∧
    (∀ i < 5, r_inv[i]!.val ≤ 2^51 + (2^13 - 1) * 19) := by
  unfold negate
  progress*
  · simp_all; grind
  · simp_all; grind
  · simp_all; grind
  · simp_all; grind
  · simp_all; grind
  constructor
  · have : 16 * p =
      36028797018963664 * 2^0 +
      36028797018963952 * 2^51 +
      36028797018963952 * 2^102 +
      36028797018963952 * 2^153 +
      36028797018963952 * 2^204 := by simp [p]
    simp_all [Nat.ModEq, Field51_as_Nat, Finset.sum_range_succ, Array.make, Array.getElem!_Nat_eq]
    grind
  · assumption
```

## Example function: `add`

[Code on this slide to be made small, just shown to give an impression]

```lean
set_option maxHeartbeats 1000000 in
-- probably the simp_all is heavy
/-- **Spec for `backend.serial.u64.scalar.Scalar52.add_loop`**:
- Starting from index `i` with accumulator `sum` and carry `carry`
- Computes limb-wise addition with carry propagation
- Result limbs are bounded by 2^52
- Parts of sum before index i are preserved
- The result satisfies the modular arithmetic property -/
@[progress]
theorem add_loop_spec (a b sum : Scalar52) (mask carry : U64) (i : Usize)
    (ha : ∀ j < 5, a[j]!.val < 2 ^ 52) (hb : ∀ j < 5, b[j]!.val < 2 ^ 52)
    (ha' : Scalar52_as_Nat a < 2 ^ 259) (hb' : Scalar52_as_Nat b < 2 ^ 259)
    (hmask : mask.val = 2 ^ 52 - 1) (hi : i.val ≤ 5)
    (hcarry : i.val = 5 → carry.val < 2 ^ 52)
    (hcarry : ∀ i < 5, carry.val < 2 ^ 53)
    (hsum : ∀ j < 5, sum[j]!.val < 2 ^ 52)
    (hsum' : ∀ j < 5, i.val ≤ j → sum[j]!.val = 0) :
    ∃ sum', add_loop a b sum mask carry i = ok sum' ∧
    (∀ j < 5, sum'[j]!.val < 2 ^ 52) ∧
    (∀ j < i.val, sum'[j]!.val = sum[j]!.val) ∧
    ∑ j ∈ Finset.Ico i.val 5, 2 ^ (52 * j) * sum'[j]!.val =
      ∑ j ∈ Finset.Ico i.val 5, 2 ^ (52 * j) * (a[j]!.val + b[j]!.val) +
      2 ^ (52 * i.val) * (carry.val / 2 ^ 52) := by
  unfold add_loop
  unfold Indexcurve25519_dalekbackendserialu64scalarScalar52UsizeU64.index
  unfold IndexMutcurve25519_dalekbackendserialu64scalarScalar52UsizeU64.index_mut
  progress*
  · have := ha i (by scalar_tac)
    have := hb i (by scalar_tac)
    scalar_tac
  · have := ha i (by scalar_tac)
    have := hb i (by scalar_tac)
    scalar_tac
  · intro hi
    have : i.val = 4 := by grind
    have : a[4]!.val < 2 ^ 51 := by grind [Scalar52_top_limb_lt_of_as_Nat_lt]
    have : b[4]!.val < 2 ^ 51 := by grind [Scalar52_top_limb_lt_of_as_Nat_lt]
    simp [*]
    have : carry.val >>> 52 ≤ 1 := by have := hcarry i (by scalar_tac); omega
    simp at *; grind
  · intro j hj
    have : carry.val >>> 52 ≤ 1 := by have := hcarry i (by scalar_tac); omega
    have := ha i (by scalar_tac)
    have := hb i (by scalar_tac)
    simp at *; grind
  · intro j hj
    by_cases hc : j = i
    · rw [hc]
      have := Array.set_of_eq sum i5 i (by scalar_tac)
      simp only [UScalar.ofNat_val, Array.getElem!_Nat_eq, Array.set_val_eq, gt_iff_lt] at this ⊢
      simp [this, i5_post_1, hmask]
      grind
    · have := Array.set_of_ne sum i5 j i (by scalar_tac) (by scalar_tac) (by grind)
      have := hsum j (by scalar_tac)
      simp_all
  · intro j hj _
    have hne : j ≠ i := by grind
    have := Array.set_of_ne' sum i5 j i (by scalar_tac) (by omega)
    have := hsum' j hj (by omega)
    simp_all
  · refine ⟨?_, ?_, ?_⟩
    · grind
    · intro j hj
      have := res_post_2 j (by omega)
      have := Array.set_of_ne sum i5 j i (by scalar_tac) (by scalar_tac) (by omega)
      simp_all
    · have : carry1.val = a[i]!.val + b[i]!.val + carry.val / 2 ^ 52 := by
        simp [*]; omega
      have : res[i]! = carry1.val % 2 ^ 52 := by
        have := res_post_2 i.val (by omega)
        have := Array.set_of_eq sum i5 i (by scalar_tac)
        simp_all
      have : ∑ j ∈ Finset.Ico (i.val + 1) 5, 2 ^ (52 * j) * res[j]!.val =
          ∑ j ∈ Finset.Ico (i.val + 1) 5, 2 ^ (52 * j) * ((a)[j]!.val + (b)[j]!.val) +
          2 ^ (52 * (i.val + 1)) * (↑carry1 / 2 ^ 52) := by
        have : 4503599627370496 = 2 ^ 52 := by grind
        simp_all
      have : 2 ^ (52 * i.val) * (carry1.val % 2 ^ 52) +
          2 ^ (52 * (i.val + 1)) * (carry1.val / 2 ^ 52) = 2 ^ (52 * i.val) * carry1.val := by
        have : carry1.val % 2 ^ 52 + 2 ^ 52 * (carry1.val / 2 ^ 52) = carry1.val := by grind
        grind
      calc ∑ j ∈ Finset.Ico (↑i) 5, 2 ^ (52 * j) * res[j]!
        _ = 2 ^ (52 * ↑i) * res[i]! +
            ∑ j ∈ Finset.Ico (↑i + 1) 5, 2 ^ (52 * j) * res[j]! := by
          have hi : i.val < 5 := by scalar_tac
          simp [Finset.sum_eq_sum_Ico_succ_bot hi]
        _ = ∑ j ∈ Finset.Ico (↑i) 5, 2 ^ (52 * j) * (↑a[j]! + ↑b[j]!) +
            2 ^ (52 * ↑i) * (↑carry / 2 ^ 52) := by
          have hi : i.val < 5 := by scalar_tac
          rw [Finset.sum_eq_sum_Ico_succ_bot hi]
          grind
  · refine ⟨?_, fun j hj ↦ ?_, ?_⟩
    · grind
    · simp
    · have : i.val = 5 := by scalar_tac
      simp [this]; grind
termination_by 5 - i.val
decreasing_by scalar_decr_tac
```

```lean
/-- **Spec and proof concerning `scalar.Scalar52.add`**:
- Requires the input values to be bounded by  2 ^ 259
- The result represents the sum of the two input scalars modulo L
-/
@[progress]
theorem add_spec (a b : Scalar52) (ha : ∀ i < 5, a[i]!.val < 2 ^ 52) (hb : ∀ i < 5, b[i]!.val < 2 ^ 52)
    (ha' : Scalar52_as_Nat a < 2 ^ 259) (hb' : Scalar52_as_Nat b < 2 ^ 259) :
    ∃ v, add a b = ok v ∧
    Scalar52_as_Nat v % L = (Scalar52_as_Nat a + Scalar52_as_Nat b) % L := by
  unfold add
  progress*
  · intro j _
    unfold ZERO
    interval_cases j <;> decide
  · unfold ZERO; decide
  · intro i hi
    unfold constants.L
    interval_cases i <;> decide
  · rw [constants.L_spec] at res_post
    have h1 : Scalar52_as_Nat res ≡ Scalar52_as_Nat sum [MOD L] := by
      have hL_mod : L ≡ 0 [MOD L] := by
        rw [Nat.ModEq, Nat.zero_mod, Nat.mod_self]
      have : Scalar52_as_Nat res + L ≡ Scalar52_as_Nat res + 0 [MOD L] :=
        Nat.ModEq.add_left _ hL_mod
      simp only [add_zero] at this
      exact this.symm.trans res_post
    have h2 : Scalar52_as_Nat sum = Scalar52_as_Nat a + Scalar52_as_Nat b := by
      unfold Scalar52_as_Nat
      simp only [Finset.range_eq_Ico] at sum_post_3 ⊢
      conv_lhs => rw [sum_post_3]
      simp [Finset.sum_add_distrib, Nat.mul_add]
    rw [h1, h2]
```

## Expressive specs

- Not using RFCs for the specs 
- Working with the rich mathematical structure of the Edwards curve
- 9 different representations: 
    - backend.serial.curve_models.ProjectivePoint
    - backend.serial.curve_models.CompletedPoint
    - backend.serial.curve_models.ProjectiveNielsPoint
    - edwards.EdwardsPoint
    - edwards.affine.AffinePoint
    - edwards.CompressedEdwardsY
    - montgomery.MontgomeryPoint
    - ristretto.RistrettoPoint
    - ristretto.CompressedRistretto
- Conversion functions

## Example function: `double`

```lean
theorem double_spec (q : ProjectivePoint)
    (h_qX_bounds : ∀ i < 5, (q.X[i]!).val ≤ 2 ^ 52)
    (h_qY_bounds : ∀ i < 5, (q.Y[i]!).val ≤ 2 ^ 52)
    (h_qZ_bounds : ∀ i < 5, (q.Z[i]!).val ≤ 2 ^ 52) :
    ∃ c, double q = ok c ∧
    let X := Field51_as_Nat q.X
    let Y := Field51_as_Nat q.Y
    let Z := Field51_as_Nat q.Z
    let X' := Field51_as_Nat c.X
    let Y' := Field51_as_Nat c.Y
    let Z' := Field51_as_Nat c.Z
    let T' := Field51_as_Nat c.T
    X' % p = (2 * X * Y) % p ∧
    Y' % p = (Y^2 + X^2) % p ∧
    (Z' + X^2) % p = Y^2 % p ∧
    (T' + Z') % p = (2 * Z^2) % p := by
  sorry
```

```lean
theorem double_spec' (q : ProjectivePoint) (hq_valid : q.IsValid) :
    ∃ c, ProjectivePoint.double q = ok c ∧ c.IsValid ∧
    (c : Point Ed25519) = q + q := by
  sorry
```

## Process overview

1. Implementation
2. Spec theorem statements (internal & public functions)
3. Spec theorem proofs

- Goal 1: suppose 1. & 2. exist and are correct, easily produce 3.
- Different approaches:
  - Implementation togeher with spec statements
  - Implementation -> spec statements
  - Spec statements -> Implementation

## Next steps

- Migrating to `mvcgen`
- Complete the proofs of this crate
- Look at another crate with slightly different character

## Refinements 

- Axioms for external functions? Or implementations?
- Presentation of spec statements? Verso within Rust docs?
- Systematically testing extraction issues

## Trust model

To trust that the curve25519-dalek implementation satisfies the proven specifications, you need to trust:
1. The Lean Proof Checker

    Lean’s minimal trusted kernel guarantees absolute correctness in the proofs

2. The Aeneas Translation

    One needs to know that the Lean code extracted by Aeneas faithfully represents the Rust code, this is a limited set of translations and subject to ongoing soundness proofs

3. The Specifications

    The specifications are written in Lean which allows a phrasing which is convenient for humans to parse and allows easy drilling down into details using the interactive feature of Lean

4. External specifications

    External dependencies of the crate have specs written in FunsExternal.lean and TypesExternal.lean so these files need to be inspected to ensure that these specs are correct

## Annoying details 

- E.g., `a = limbs.set i i2`
- E.g., `>>>` with `grind`
- E.g., proofs depend on variable names introduced by tactic, makes proof fragile
- E.g., uses `Aeneas.Std.Array` which isn't the standard array and we don't benefit from the established API


## Conclusions 

- The toolchain works
- Great that you can see the goal during creation of proof, can start to do the proof manually, explore the proof, use simp, etc.


It works but we can already glimpse the amazing!

The challenge: Given correct spec theorem, the proof is automatic.
