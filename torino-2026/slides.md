---
theme: default
title: Verifying curve25519-dalek using Lean
info: |
  Torino Rust Verification Workshop, 14 April 2026
  Oliver Butterley - The Beneficial AI Foundation & University of Rome Tor Vergata
class: text-center
highlighter: shiki
drawings:
  persist: false
transition: slide-left
mdc: true
layout: cover
---

<h1 class="text-4xl">Verifying curve25519-dalek using Lean</h1>

**Oliver Butterley, Markus Dablander, Alessandro D'Angelo, Hoang Le Truong, Liao Zhang**



<div class="mt-4 flex justify-center items-center">
  <div class="bg-gray-800 px-3 py-2 rounded">
    <img src="/images/BAIF_Logo.png" class="h-12" />
  </div>
</div>

<div class="abs-bottom mb-8 opacity-50">

Rust Verification Workshop, Turin 14 April 2026

</div>

<!--
Good afternoon everyone. I'm Oliver Butterley and I'm going to talk about our experience verifying curve25519-dalek using Lean — a project we've been working on at the Beneficial AI Foundation.
-->

---

## The Beneficial AI Foundation

One core mission: making formal verification easier, cheaper and ubiquitous.

## Lean-Dalek Team

<div class="flex gap-6 mt-4 justify-center">
  <div class="flex flex-col items-center gap-1">
    <img src="https://github.com/oliver-butterley.png" class="w-14 h-14 rounded-full" />
    <span class="text-sm"><strong>Oliver Butterley</strong></span>
    <span class="text-xs opacity-40">@oliver-butterley</span>
  </div>
  <div class="flex flex-col items-center gap-1">
    <img src="https://github.com/MarkusFerdinandDablander.png" class="w-14 h-14 rounded-full" />
    <span class="text-sm"><strong>Markus Dablander</strong></span>
    <span class="text-xs opacity-40">@MarkusFerdinandDablander</span>
  </div>
  <div class="flex flex-col items-center gap-1">
    <img src="https://github.com/a-dangelo.png" class="w-14 h-14 rounded-full" />
    <span class="text-sm"><strong>Alessandro D'Angelo</strong></span>
    <span class="text-xs opacity-40">@a-dangelo</span>
  </div>
  <div class="flex flex-col items-center gap-1">
    <img src="https://github.com/truonghoangle.png" class="w-14 h-14 rounded-full" />
    <span class="text-sm"><strong>Hoang Le Truong</strong></span>
    <span class="text-xs opacity-40">@truonghoangle</span>
  </div>
  <div class="flex flex-col items-center gap-1">
    <img src="https://www.gravatar.com/avatar/zhangliao714?d=identicon&f=y&s=112" class="w-14 h-14 rounded-full" />
    <span class="text-sm"><strong>Liao Zhang</strong></span>
    <span class="text-xs opacity-40">@zhangliao714</span>
  </div>
</div>

<!--
Jure already introduced the Beneficial AI Foundation so I'll be brief. The foundation's mission is ensuring AI benefits humanity, and one concrete effort is formally verifying critical open-source infrastructure. This is the team working on the curve25519-dalek verification — five of us, a mix of mathematicians and computer scientists.
-->

---

## Overview

What follows is our **real-world experience** of verifying the functional correctness of production Rust cryptography code in Lean.

<div class="mt-6">

1. **Background:** verification target, toolchain, Lean proofs
2. **Extraction issues:** what breaks when you try to extract real Rust
3. **Proof engineering:** what breaks when you try to prove at scale
4. **Contributions** to open-source verification infrastructure

</div>

<div class="mt-4 text-sm opacity-70">

Project repo: https://github.com/Beneficial-AI-Foundation/curve25519-dalek-lean-verify

</div>

<!--
The aim of this talk is to share real-world experience. Not the theory of how this should work, but what actually happens when you try to verify a production Rust crate end-to-end. I'll cover two main categories of difficulties: extraction issues — the gap between Rust as written and what Aeneas can handle — and proof engineering — the performance and scaling challenges once you're in Lean. And I want to emphasise the upstreaming culture: we contribute back to the tools we depend on.
-->

---

## The task: curve25519-dalek

<div class="grid grid-cols-2 gap-6 mt-2">
<div>

- Pure Rust library for **elliptic curve primitives**, focussing on speed
- ~33k LOC
- Multiple backends, we focus on the **serial/u64 backend**
- Low control-flow complexity, **high data-complexity**
- E.g., Bit-level manipulations on 5×u64 limb representations
- E.g., constructors and operations that guarantee that curve points stay as curve points

<div class="mt-4 text-sm opacity-70">

</div>

</div>
<div>

```rust
/// Reduce to enforce bound 2^(51 + epsilon).
fn reduce(mut limbs: [u64; 5]) -> [u64; 5] {
    const LOW_51_BIT_MASK: u64 =
        (1u64 << 51) - 1;

    let c0 = limbs[0] >> 51;
    let c1 = limbs[1] >> 51;
    let c2 = limbs[2] >> 51;
    let c3 = limbs[3] >> 51;
    let c4 = limbs[4] >> 51;

    limbs[0] &= LOW_51_BIT_MASK;
    limbs[1] &= LOW_51_BIT_MASK;
    // ...
    limbs[0] += c4 * 19; // 2^255 ≡ 19
    limbs[1] += c0;
    // ...
    limbs
}
```

</div>
</div>

<!--
Jure already introduced curve25519-dalek in his talk, so I'll just highlight the character of the code we're verifying. It's about 33 thousand lines total, but we specifically target the serial 64-bit backend — around 9 thousand lines. The code has low control-flow complexity — you won't find deeply nested conditionals or complex dispatch. But the data complexity is high: everything is bit-level manipulation on arrays of 64-bit limbs. Here you see the reduce function — shifts, masks, carries, and that magic constant 19 coming from the fact that 2 to the 255 is congruent to 19 modulo p.
-->

---

## Extraction: Rust to Lean

<img src="/pipeline.svg" class="h-44 mx-auto mt-4" />

<div class="mt-4 text-sm">

**The Lean model** faithfully captures Rust semantics:
- `Result` monad — every operation can succeed (`ok`), fail (`fail`), or diverge (`div`)
- Arithmetic operations are fallible (overflow checking), etc.
- Imperative code via `do`-notation with monadic bind
- `Funs.lean`: in our project 8,176 lines of extracted function definitions

</div>

<!--
The extraction pipeline was covered earlier today so I'll move through this quickly. Rust source goes through Charon, which extracts from MIR and produces a single dense LLBC file — a JSON representation of the program with no whitespace. Then Aeneas reads this and generates Lean code: Funs.lean with over 8,000 lines of extracted function definitions, and Types.lean with the type definitions. The Lean model faithfully captures Rust semantics — every arithmetic operation is wrapped in a Result monad because it could overflow, and imperative code is expressed using do-notation with monadic bind.
In Dante's Divine Comedy, Charon forces reluctant sinners onto his boat by beating them with his oar.
Charon also ferried the living mortals Aeneas to the underworld and back again. 
-->

---

<img src="/images/Gustave_Doré_-_Dante_Alighieri_-_Inferno_-_Plate_10_(Canto_III_-_Charon_herds_the_sinners_onto_his_boat).jpg" class="h-100 mx-auto" />

<div class="text-center text-sm opacity-70 mt-1">

In Dante's Divine Comedy, Charon forces reluctant sinners onto his boat by beating them with his oar.

</div>

<!--
Since we are in Italy, we have to mention Dante. Here is Gustave Doré's famous illustration of Charon from the Inferno — herding reluctant sinners onto his boat, beating them with his oar. And of course Charon also ferried the living hero Aeneas to the underworld and back — so our two tools are connected by mythology as well as by our pipeline.
-->

---

## Proofs in Lean

```lean
theorem reduce_spec (limbs : Array U64 5#usize) :
    reduce limbs ⦃ (result : FieldElement51) =>
      (∀ i < 5, result[i]!.val < 2 ^ 52) ∧
      Field51_as_Nat limbs ≡ Field51_as_Nat result [MOD p] ⦄ := by
  unfold reduce
  step*
  · simp [*]; scalar_tac        -- ⊢ ↑i15 + ↑i14 ≤ U64.max
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · simp [*]; scalar_tac
  · constructor
    · intro i _                 -- ∀ i < 5, result limbs < 2^52
      interval_cases i
      all_goals simp [*]; scalar_tac
    · simp [Field51_as_Nat, Finset.sum_range_succ, p, Nat.ModEq, *]
      omega
```

<div class="text-sm mt-2 opacity-80">

The spec states: the function succeeds, all output limbs are bounded, and the result equals the input mod p. The proof unfolds the function, uses `step*` to process each extracted operation, then discharges overflow and correctness goals.

</div>

<!--
This is what a proof actually looks like. At the top, the spec theorem states what reduce must satisfy: it succeeds — no overflow — all output limbs stay below 2 to the 52, and the mathematical value is preserved modulo p. The proof unfolds the function definition, then `step*` — a tactic from the Aeneas library — processes each extracted operation one by one. It generates side goals for each arithmetic operation that could overflow, which we discharge with `simp` and `scalar_tac`. The final goals are the actual mathematical properties. This is the interactive theorem prover experience: you write the spec, unfold the function, and the system guides you through exactly what needs to be proved.
-->

---

## Project status

**192 functions** in total

<img src="/images/progress_2026-04-10.png" class="h-80 mx-auto mt-4" />

<!--
Here's where we stand. 192 functions in scope. You can see the progress over time — the green area is verified functions, steadily climbing. We're now approaching full coverage.
-->

---

## Extraction issues (1/2)

<div class="mt-2">

### Patterns Aeneas cannot extract

**Dynamic array indexing** — `output[i] = value` where `i` is computed at runtime:
- `non_adjacent_form`, `as_radix_2w` in `scalar.rs` cause Aeneas internal errors
- All downstream dependents excluded via `#[cfg(not(verify))]`

**Iterator patterns** — `.map()`, `.rev()`, `.skip()`, `impl Iterator` parameters:
- `bits_le()`, `mul_bits_be()` rely on iterator trait machinery
- Fundamentally incompatible with current extraction

**For-loops** — must be rewritten as while-loops:

</div>

<div class="grid grid-cols-2 gap-4 mt-1">
<div>

```rust
// Before (idiomatic Rust)
for i in 0..5 {
    self.0[i] += _rhs.0[i];
}
```

</div>
<div>

```rust
// After (Aeneas-compatible)
let mut i = 0;
while i < 5 {
    self.0[i] += _rhs.0[i];
    i += 1;
}
```

</div>
</div>

<!--
Let me walk through the extraction issues — the gap between idiomatic Rust and what Charon and Aeneas can actually handle. First: dynamic array indexing. If you write `output[i] = value` where i is computed at runtime, Aeneas hits an internal error. Two functions in scalar.rs — non_adjacent_form and as_radix_2w — have this pattern, and we had to exclude them and all their callers. Second: iterators. Anything using `.map()`, `.rev()`, the Iterator trait — Aeneas can't model this. And third: for-loops. Every `for i in 0..n` has to become a while-loop. It's mechanical but it touches a lot of code.
-->

---

## Extraction issues (2/2)

**ConditionallyNegatable** — trait not extractable, must be decomposed:

```rust
// Before: x.conditional_negate(choice);
// After:
let x_neg = -&x;
x.conditional_assign(&x_neg, choice);
```

**`#[cfg(not(verify))]` gating** — exclude what can't be extracted, keep what can.

### Case study: Montgomery scalar multiplication

```rust
// Original: chains three iterator adapters
self.mul_bits_be(scalar.bits_le().rev().skip(1))
// Rewritten: inline Montgomery ladder with direct byte/bit indexing
let mut i: isize = 254;
while i >= 0 {
    let byte_idx = (i >> 3) as usize;
    let bit_idx = (i & 7) as usize;
    let cur_bit = ((scalar_bytes[byte_idx] >> bit_idx) & 1u8) == 1u8;
    // ... Montgomery ladder step ...
    i -= 1;
}
```

<div class="text-sm mt-2 opacity-70">

Total: 879-line diff on a 9,700-line codebase (~9% modified). Only variable-time optimised paths are excluded — all core arithmetic, point operations, and compression/decompression are verified.

</div>

<!--
More extraction issues. The ConditionallyNegatable trait from the subtle crate can't be extracted — we decompose it into conditional_assign plus an explicit negation. We gate excluded code with cfg not verify, set via Cargo config.

The most interesting case study is Montgomery scalar multiplication. The original code chains three iterator adapters: bits_le, rev, skip. Completely idiomatic Rust, completely unextractable. We rewrote it as an inline while loop that walks the scalar bytes directly, extracting bits with shifts and masks. This let us verify the most important Montgomery operation.

In total, the diff is 879 lines on a 9,700-line codebase — about 9 percent. But importantly, only the variable-time optimised multiplication paths are excluded. All core arithmetic, all point operations, compression and decompression — all verified.
-->

---

## Proof issues (1/2)

### Heartbeat escalation

- Lean's default: **200,000** heartbeats
- Our proofs require up to **14,000,000** (70x default)
- Why: `step*` unfolds deeply nested extracted code; `simp` struggles with large intermediate terms

```lean
set_option maxHeartbeats 14000000 in
theorem mul_spec ...
```

### Large number literals

- Curve constants are 78-digit numbers (e.g. `sqrt(-1)` in the field)
- Kernel elaboration consumes **20+ GB RAM** trying to normalise these
- `ring` and `decide` time out
- The remaining `sorry` in `Math/` are all of this character (5 total)

<!--
Now let's talk about what happens once extraction works and you're actually in Lean trying to prove things. The first problem is heartbeats. Lean has a default computation budget of 200,000 heartbeats. Our proofs need up to 14 million — that's 70 times the default. The reason is that `step*` unfolds the extracted code step by step, and each step can leave large intermediate terms that `simp` has to process.

The second problem is large number literals. The curve constants — like the square root of minus one in the field — are 78-digit numbers. When Lean's kernel tries to normalise expressions involving these, it can consume over 20 gigabytes of RAM. The ring tactic times out. The decide tactic times out. The five remaining sorry statements in our mathematical library are all of this character — we know the proofs are correct, we just can't get Lean to check them in bounded memory.
-->

---

## Proof issues (2/2)

### Bridge lemma pattern

Factor expensive ring normalisations into reusable intermediate lemmas:

```lean
-- Instead of letting `ring` handle the full expression, factor it:
private lemma bridge_mul {a b c : FieldElement51}
    (h : Field51_as_Nat a ≡ Field51_as_Nat b * Field51_as_Nat c [MOD p]) :
    a.toField = b.toField * c.toField := by
  unfold FieldElement51.toField
  simpa only [Nat.cast_mul] using lift_mod_eq _ _ h
```

### Hold wrapper pattern

Hide expensive hypotheses from `simp` to prevent timeouts:

```lean
private def Hold (P : Prop) : Prop := P  -- opaque to simp

-- Before calling step on an expensive function:
have h_mod : Hold (...expensive...) := h_original
clear h_original
step as ⟨result, h_post⟩    -- simp doesn't touch Hold hypotheses
change ...expensive... at h_mod  -- recover via definitional equality
```

<!--
Here are two engineering techniques we developed. First, bridge lemmas. When you have a large polynomial expression — say a schoolbook multiplication expanded over five limbs — the ring tactic times out trying to normalise it directly. So we factor the normalisation into small reusable bridge lemmas: bridge_mul, bridge_sq, bridge_sub, bridge_neg, and so on. Each one is cheap to prove, and together they let us build up the full proof without any single expensive step.

Second, the Hold wrapper. The step tactic runs simp on all hypotheses in the context. After processing a function like to_bytes, you end up with postconditions involving expensive terms. Any subsequent step call times out because simp tries to reduce these. The fix: wrap the expensive hypothesis in an opaque Hold definition before calling step. Simp can't see through it. Then afterwards, recover the original proposition via definitional equality with change. It's zero proof obligation — purely a performance trick. This pattern is universally useful for anyone doing Lean verification at scale.
-->

---

## Upstreaming

<div class="mt-4">

**Culture of contributing back to the tools we depend on.**

**Contributions to Aeneas** (6 PRs merged):
- Docstring generation, Rust visibility in Lean output, `-version` flag
- Replace custom `List.slice` with upstream `List.extract`
- Fix for `progress` tactic matching

**Issues filed** — Charon (6) and Aeneas (8+):
- Exponential slowdown extracting `generic-array` with `typenum`
- Wrapping shifts produce undefined `U64.shr` in Lean output
- Scalar `Eq` generates `=` (Prop) instead of `==` (Bool)
- Circular dependency between `Types` and `TypesExternal`

**Next:**
- Upstream Lean models of Rust core types and operations
- Continue isolating and reporting extraction edge cases to support the Aeneas/Charon developers

</div>

<!--
I want to emphasise the upstreaming culture. This isn't just about our project — we contribute back to the ecosystem. We've merged six PRs into Aeneas: better docstring generation, showing Rust visibility in Lean output, a version flag, replacing custom implementations with upstream equivalents, and a fix for the progress tactic. We've filed six issues against Charon and eight or more against Aeneas — things like exponential slowdown with typenum, wrapping shift bugs, codegen issues. Each one we try to isolate into a minimal reproducer so the Aeneas and Charon maintainers can act on it efficiently.

Going forward, we're planning to upstream our Lean models of Rust core types and operations, so other verification projects can reuse them. The Lean community has a strong upstreaming culture — definitions go to Mathlib, tool improvements go to Aeneas — and we want to be part of that.
-->

---

## Conclusions

<div class="mt-4">

**The Charon/Aeneas/Lean toolchain works for production cryptographic Rust.**

- 84% of functions fully verified, 87% including external verification
- Core arithmetic, point operations, compression/decompression — all proven correct

**Key lessons for Rust verification practitioners:**

- Plan for **iterator elimination** and **loop rewriting** from the start
- Trait boundaries (ConditionallyNegatable, Iterator) are the extraction frontier
- Proof performance requires **engineering** — bridge lemmas, Hold wrapper, heartbeat tuning
- `#[cfg(not(verify))]` is a practical, incremental gating strategy

**What's next:**
- Complete remaining 20 function proofs
- Resolve the 5 large-number `sorry` in mathematical foundations
- Explore verification of additional crates in the libsignal dependency tree

</div>

<!--
To wrap up. The toolchain works. We've verified 84 percent of curve25519-dalek's functions — all the core arithmetic, point operations, compression and decompression. The key lessons: plan for iterator elimination from the start. Know that trait boundaries are the extraction frontier. And proof performance at this scale requires real engineering — bridge lemmas, the Hold wrapper, careful heartbeat tuning. These aren't theoretical concerns, they're daily realities.

What's next: completing the remaining 20 proofs, resolving those 5 sorry statements where Lean's kernel can't handle 78-digit numbers, and moving on to additional crates in the libsignal dependency tree. Thank you.
-->

---
layout: center
class: text-center
---

## Thank you


<img src="/images/dalek-logo-clear.png" class="h-28 mx-auto mt-6 opacity-60" />


<div class="mt-6">

**Repo:** https://github.com/Beneficial-AI-Foundation/curve25519-dalek-lean-verify

</div>
