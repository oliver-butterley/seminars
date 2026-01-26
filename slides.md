---
theme: default
title: Large scale verification of production cryptography code using Lean
info: |
  Bonn, 27 January 2026
  Oliver Butterley - The Beneficial AI Foundation & University of Rome Tor Vergata
class: text-center
highlighter: shiki
drawings:
  persist: false
transition: slide-left
mdc: true
layout: cover
---

<h1 class="text-4xl">Large scale verification of production cryptography code using Lean</h1>

**Oliver Butterley**

<div class="opacity-80">

The Beneficial AI Foundation & University of Rome Tor Vergata

</div>

<div class="mt-4 flex justify-center gap-8 items-center">
  <div class="bg-gray-800 px-3 py-2 rounded">
    <img src="/images/BAIF_Logo.png" class="h-12" />
  </div>
  <div class="border-2 border-gray-300 px-3 py-2 rounded">
    <img src="/images/Tor_Vergata_Logo.png" class="h-12" />
  </div>
</div>

<div class="mt-6 text-sm opacity-70">

Project team: Alessandro D'Angelo, Hoang Le Truong, Markus Ferdinand Dablander, Zhang-Liao

</div>

<div class="abs-bottom mb-8 opacity-50">

Bonn, 27 January 2026

</div>

---

# Outline

<Toc minDepth="2" maxDepth="2" />


---
footer: 'Repo: https://github.com/Beneficial-AI-Foundation/curve25519-dalek-lean-verify'
---

**The project:**
- Functional correctness verification of (the Rust crate curve25519-dalek using Aeneas) and Lean

**Motives:**
- Part of the goal of verifying libsignal + dependencies
- Scaling verification (easier, cheaper and commonplace)

We choose Rust verified in Lean via Aeneas because it is the most relevant combination today

---

## A Rust crate of cryptographic primitives: curve25519-dalek

- Provides fast, safe cryptographic primitives (elliptic curve cryptography) used by thousands of projects for key agreement, signatures and zero-knowledge proofs
- Structures to describe points on the elliptic curve, scalars, functions for manipulating them fast
- ~200 functions

---

<img src="/images/graph.png" class="h-full w-full object-contain" />

---

### Big numbers

- Large prime
    ```lean
    /-- Curve25519 is the elliptic curve over the prime field with order `p` -/
    def p : Nat := 2^255 - 19
    ```
- The elliptic curve uses coordinates in ℤ mod p 
- Array of 5 64-bit limbs representing numbers in radix 2^51
    ```lean 
    def Field51_as_Nat (limbs : Array U64 5) : Nat :=
    ∑ i ∈ Finset.range 5, 2^(51 * i) * limbs[i].val
    ```
- Allows "space" to do calculations in place, growing up to `2^54` between reductions to `2^52`.

---

### Example function: `reduce`

```rust
pub struct FieldElement51(pub(crate) [u64; 5]);
/// Given 64-bit input limbs, reduce to enforce the bound 2^(51 + epsilon).
fn reduce(mut limbs: [u64; 5]) -> FieldElement51 {
    const LOW_51_BIT_MASK: u64 = (1u64 << 51) - 1;

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

<!-- // Since the input limbs are bounded by 2^64, the biggest
// carry-out is bounded by 2^13.
//
// The biggest carry-in is c4 * 19, resulting in
//
// 2^51 + 19*2^13 < 2^51.0000000001
//
// Because we don't need to canonicalize, only to reduce the
// limb sizes, it's OK to do a "weak reduction" -->

<!-- - Quick algorithms for manipulations mod `2^255 - 19` -->

---

### Example function: `negate`

```rust
/// Invert the sign of this field element
pub fn negate(&mut self) {
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

---

### Example function: `double`

```rust
pub struct ProjectivePoint {
    pub X: FieldElement51,
    pub Y: FieldElement51,
    pub Z: FieldElement51,
}

pub struct CompletedPoint {
    pub X: FieldElement51,
    pub Y: FieldElement51,
    pub Z: FieldElement51,
    pub T: FieldElement51,
}
```
--- 

```rust
impl ProjectivePoint {
    /// Double this point: return self + self
    pub fn double(&self) -> CompletedPoint {
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

<!-- TODO: arrange so that this fits on previous slide -->

Structures to conveniently encode a point on the elliptic curve

---

### Example function: `add` 

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

Subtle differences in each part of the code

---

## Lean model of Rust code

- Rust code can fail (overflow/underflow/etc.) 
  ```lean
  inductive Result (α : Type u) where
  | ok (v: α): Result α
  | fail (e: Error): Result α
  | div
  ```
- Rust code is imperative, imperative code in Lean (do notation with monadic bind):
  ```lean
  -- Simple function to double a natural number
  def double (n : Nat) : Result Nat := do
    let sum ← n + n           -- Add n to itself
    ok sum                    -- Wrap in Result.ok
  ```
- Aeneas is a tool which takes Rust code and extracts a model of that code in Lean (see following slide).


---

```lean
/-- Source: 'curve25519-dalek/src/backend/serial/u64/field.rs', lines 292:4-325:5 -/
def backend.serial.u64.field.FieldElement51.reduce
(limbs : Array U64 5#usize) :
Result backend.serial.u64.field.FieldElement51
:= do
let i ← Array.index_usize limbs 0#usize
let c0 ← i >>> 51#i32
let i1 ← Array.index_usize limbs 1#usize
-- ... Similar for other limbs
let i5 ←
    (↑(i &&& backend.serial.u64.field.FieldElement51.reduce.LOW_51_BIT_MASK)
    : Result U64)
let limbs1 ← Array.update limbs 0#usize i5
let i6 ← Array.index_usize limbs1 1#usize
-- ... Similar for other limbs
let i14 ← c4 * 19#u64
let i15 ← Array.index_usize limbs5 0#usize
let i16 ← i15 + i14
let limbs6 ← Array.update limbs5 0#usize i16
let i17 ← Array.index_usize limbs6 1#usize
let i18 ← i17 + c0
-- ... Similar for other limbs
let i24 ← i23 + c3
let limbs10 ← Array.update limbs9 4#usize i24
ok limbs10
```


<!-- ---

### Workflow


1. Choose a set of functions of interest
2. Choose a subset of the functions of interest
3. Modify Rust source if required
4. Extract the functions to Lean using Aeneas
5. Apply tweaks to the extracted Lean
6. Add definitions / spec theorems for external functions
7. Add spec theorem statements for every function
8. Add a proof for each spec theorem -->


---

## Spec theorems

### Example function: `U64.add`

```lean
@[progress] 
theorem U64.add_spec {x y : U64} (hmax : x.val + y.val ≤ U64.max) :
  ∃ z, x + y = ok z ∧ (↑z : Nat) = ↑x + ↑y := by ...
```

---

### Example function: `reduce`

```lean
/-- **Spec and proof concerning `FieldElement51.reduce`**:
- Does not overflow
- All limbs of result are small, ≤ 2^(51 + ε)
- Result equals input mod p -/
@[progress]
theorem reduce_spec (limbs : Array U64 5#usize) :
    ∃ result, reduce limbs = ok result ∧
    (∀ i < 5, result[i]!.val ≤ 2^51 + (2^13 - 1) * 19) ∧
    Field51_as_Nat limbs ≡ Field51_as_Nat result [MOD p] := by
  unfold reduce
  progress*
  · simp [*]; scalar_tac        -- ⊢ ↑i15 + ↑i14 ≤ U64.max
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · constructor
    · intro i _                 -- ∀ i < 5, ↑limbs10[i]! ≤ 2 ^ 51 + (2 ^ 13 - 1) * 19
      interval_cases i
      all_goals simp [*]; scalar_tac
    · simp [Field51_as_Nat, Finset.sum_range_succ, p, Nat.ModEq, *]; omega
```

---

### Example function: `negate` - Lean spec

```lean
/-- **Spec and proof concerning `FieldElement51.negate`**:
- Result r_inv is additive inverse of input r in 𝔽_p
- All limbs of result are small, ≤ 2^(51 + ε) -/
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

---

### Example function: `add` - Lean spec


```lean
@[progress]
theorem add_loop_spec (a b sum : Scalar52) (mask carry : U64) (i : Usize)
    (ha : ∀ j < 5, a[j]!.val < 2 ^ 52) (hb : ∀ j < 5, b[j]!.val < 2 ^ 52)
    (ha' : Scalar52_as_Nat a < 2 ^ 259) (hb' : Scalar52_as_Nat b < 2 ^ 259)
    (hmask : mask.val = 2 ^ 52 - 1) (hi : i.val ≤ 5) ... :
    ∃ sum', add_loop a b sum mask carry i = ok sum' ∧
    (∀ j < 5, sum'[j]!.val < 2 ^ 52) ∧
    (∀ j < i.val, sum'[j]!.val = sum[j]!.val) ∧
    ∑ j ∈ Finset.Ico i.val 5, 2 ^ (52 * j) * sum'[j]!.val =
      ∑ j ∈ Finset.Ico i.val 5, 2 ^ (52 * j) * (a[j]!.val + b[j]!.val) +
      2 ^ (52 * i.val) * (carry.val / 2 ^ 52) := by
  unfold add_loop
  progress* ...
```

```lean
@[progress]
theorem add_spec (a b : Scalar52)
    (ha : ∀ i < 5, a[i]!.val < 2 ^ 52) (hb : ∀ i < 5, b[i]!.val < 2 ^ 52)
    (ha' : Scalar52_as_Nat a < 2 ^ 259) (hb' : Scalar52_as_Nat b < 2 ^ 259) :
    ∃ v, add a b = ok v ∧
    Scalar52_as_Nat v % L = (Scalar52_as_Nat a + Scalar52_as_Nat b) % L := by
  unfold add
  progress* ...
```


---

## Expressive specs

- Not using RFCs for the specs
- Working with the mathematical structure of the Edwards curve

**Multiple different representations of the curve:**
- `backend.serial.curve_models.ProjectivePoint`
- `backend.serial.curve_models.CompletedPoint`
- `backend.serial.curve_models.ProjectiveNielsPoint`
- `edwards.EdwardsPoint`
- `edwards.affine.AffinePoint`
- `edwards.CompressedEdwardsY`
- `montgomery.MontgomeryPoint`
- `ristretto.RistrettoPoint`
- `ristretto.CompressedRistretto`

---

### Example function: `double` - Lean specs

**Low-level spec (coordinate formulas):**

```lean
theorem double_spec (q : ProjectivePoint) (bounds...) :
    ∃ c, double q = ok c ∧
    let X := Field51_as_Nat q.X; let Y := Field51_as_Nat q.Y
    let Z := Field51_as_Nat q.Z
    let X' := Field51_as_Nat c.X; let Y' := Field51_as_Nat c.Y
    let Z' := Field51_as_Nat c.Z; let T' := Field51_as_Nat c.T
    X' % p = (2 * X * Y) % p ∧
    Y' % p = (Y^2 + X^2) % p ∧
    (Z' + X^2) % p = Y^2 % p ∧
    (T' + Z') % p = (2 * Z^2) % p := by ...
```

**High-level spec (mathematical meaning):**

```lean
theorem double_spec' (q : ProjectivePoint) (hq : q.IsValid) :
    ∃ result : CompletedPoint, ProjectivePoint.double q = ok result ∧
    result.IsValid ∧
    result.toPoint = q.toPoint + q.toPoint := by ...
```


---

## Trust model

To trust that curve25519-dalek satisfies the proven specifications:

<v-clicks>

1. **The Lean Proof Checker**
   - Lean's minimal trusted kernel guarantees correctness

2. **The Aeneas Translation**
   - Lean code extracted by Aeneas faithfully represents the Rust code

3. **The Specifications**
   - Written in Lean - convenient for humans to parse
   - Easy drilling down into details using interactive features

4. **External specifications**
   - External dependencies have specs in `FunsExternal.lean` and `TypesExternal.lean`

</v-clicks>

 
---

## Tooling (repo integrity and collaboration)

Extensive CI checks

**Code integrity:**

- Check Rust code (compile, test, fmt)
- Check Lean code builds
- Confirm Aeneas extracted code hasn't been modified
- Confirm no additional modifications to Rust source

**Spec assistance and collaboration:**

- Count number specified and verified
- Build project site
- Dependency analysis
- Status view
- Links to repo issues and PRs


---

### Status Page

<img src="/status_page.png" class="h-100 mx-auto" />


---

### Progress

<img src="/images/progress.png" class="h-full w-full object-contain" />

---

## Next steps

### Process overview

1. Implementation
2. Spec theorem statements (internal & public functions)
3. Spec theorem proofs

**Goal:** Given 1. & 2. correct, easily produce 3.

**Different approaches:**
- Implementation together with spec statements
- Implementation → spec statements
- Spec statements → Implementation


---

### Refinements

- Faster version of `progress*` (or `mvcgen`)
- Complete the proofs of this crate
- Look at another crate with slightly different character
- Connect to another Lean verified crate for external functions?
- Presentation of spec statements? Lean specs within Rust docs?
- Complete support in Aeneas for Rust syntax.


---


### Conclusions

- The toolchain works
- Great that you can see the goal during creation of proof
- Can start to do the proof manually, explore the proof, etc.

<div class="mt-8 text-center text-2xl">

**It works but we can already glimpse the amazing!**

</div>

<div class="mt-4 text-center text-xl text-blue-500">

**The challenge:** Given correct spec theorems, the proofs are automatic.

</div>
