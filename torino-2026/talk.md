# Talk text — Verifying curve25519-dalek using Lean
## Torino Rust Verification Workshop, 14 April 2026

---

### Slide 1 — Title

Good afternoon everyone. I'm Oliver Butterley and I'm going to talk about our experience verifying curve25519-dalek using Lean — a project we've been working on at the Beneficial AI Foundation.

---

### Slide 2 — BAIF + Team

Jure already introduced the Beneficial AI Foundation so I'll be brief. The foundation's mission is ensuring AI benefits humanity, and one concrete effort is formally verifying critical open-source infrastructure. This is the team working on the curve25519-dalek verification — five of us, a mix of mathematicians and computer scientists.

---

### Slide 3 — Overview

The aim of this talk is to share real-world experience. Not the theory of how this should work, but what actually happens when you try to verify a production Rust crate end-to-end. I'll cover two main categories of difficulties: extraction issues — the gap between Rust as written and what Aeneas can handle — and proof engineering — the performance and scaling challenges once you're in Lean. And I want to emphasise the upstreaming culture: we contribute back to the tools we depend on.

---

### Slide 4 — The task: curve25519-dalek

Jure already introduced curve25519-dalek in his talk, so I'll just highlight the character of the code we're verifying. It's about 33 thousand lines total, but we specifically target the serial 64-bit backend — around 9 thousand lines. The code has low control-flow complexity — you won't find deeply nested conditionals or complex dispatch. But the data complexity is high: everything is bit-level manipulation on arrays of 64-bit limbs. Here you see the reduce function — shifts, masks, carries, and that magic constant 19 coming from the fact that 2 to the 255 is congruent to 19 modulo p.

---

### Slide 5 — Extraction: Rust to Lean

The pipeline was covered earlier today so I'll move through this quickly, but I want the details to be clear. Rust source goes through Charon, which extracts from MIR, then Aeneas generates Lean code. On the right you can see what the extracted Lean looks like — it's a faithful model of the Rust, every operation wrapped in the Result monad because any arithmetic could overflow. The do notation makes it read almost like the original Rust. We end up with over 8,000 lines of extracted Lean and 192 separate spec theorem files.

---

### Slide 6 — Proofs in Lean

This is what a proof actually looks like. At the top, the spec theorem states what reduce must satisfy: it succeeds — no overflow — all output limbs stay below 2 to the 52, and the mathematical value is preserved modulo p.

The proof unfolds the function definition, then `step*` — a tactic from the Aeneas library — processes each extracted operation one by one. It generates side goals for each arithmetic operation that could overflow, which we discharge with `simp` and `scalar_tac`. The final goals are the actual mathematical properties.

This is the interactive theorem prover experience: you write the spec, unfold the function, and the system guides you through exactly what needs to be proved.

---

### Slide 7 — Project status

Here's where we stand. 192 functions in scope. 161 fully verified — that's 84 percent. Five more are externally verified, meaning the proofs exist on paper or in another system and we've marked them with a special attribute. 20 are extracted but not yet proven. And 7 couldn't be extracted at all, which brings us to the extraction issues.

---

### Slide 8 — Extraction issues (1/2)

Let me walk through the extraction issues — the gap between idiomatic Rust and what Charon and Aeneas can actually handle.

First: dynamic array indexing. If you write `output[i] = value` where i is computed at runtime, Aeneas hits an internal error. Two functions in scalar.rs — non_adjacent_form and as_radix_2w — have this pattern, and we had to exclude them and all their callers.

Second: iterators. Anything using `.map()`, `.rev()`, the Iterator trait — Aeneas can't model this. This is a fundamental limitation, not just a missing feature.

And third: for-loops. Every `for i in 0..n` has to become a while-loop. It's mechanical but it touches a lot of code. You can see the before and after — it's not complicated, but it's everywhere.

---

### Slide 9 — Extraction issues (2/2)

More extraction issues. The ConditionallyNegatable trait from the subtle crate can't be extracted — we decompose it into conditional_assign plus an explicit negation. We gate excluded code with `cfg(not(verify))`, set via Cargo config.

The most interesting case study is Montgomery scalar multiplication. The original code chains three iterator adapters: `bits_le`, `rev`, `skip`. Completely idiomatic Rust, completely unextractable. We rewrote it as an inline while loop that walks the scalar bytes directly, extracting bits with shifts and masks. This let us verify the most important Montgomery operation.

In total, the diff is 879 lines on a 9,700-line codebase — about 9 percent. But importantly, only the variable-time optimised multiplication paths are excluded. All core arithmetic, all point operations, compression and decompression — all verified.

---

### Slide 10 — Proof issues (1/2)

Now let's talk about what happens once extraction works and you're actually in Lean trying to prove things.

The first problem is heartbeats. Lean has a default computation budget of 200,000 heartbeats. Our proofs need up to 14 million — that's 70 times the default. The reason is that `step*` unfolds the extracted code step by step, and each step can leave large intermediate terms that `simp` has to process.

The second problem is large number literals. The curve constants — like the square root of minus one in the field — are 78-digit numbers. When Lean's kernel tries to normalise expressions involving these, it can consume over 20 gigabytes of RAM. The ring tactic times out. The decide tactic times out. The five remaining sorry statements in our mathematical library are all of this character — we know the proofs are correct, we just can't get Lean to check them in bounded memory.

---

### Slide 11 — Proof issues (2/2)

Here are two engineering techniques we developed.

First, bridge lemmas. When you have a large polynomial expression — say a schoolbook multiplication expanded over five limbs — the ring tactic times out trying to normalise it directly. So we factor the normalisation into small reusable bridge lemmas: bridge_mul, bridge_sq, bridge_sub, bridge_neg, and so on. Each one is cheap to prove, and together they let us build up the full proof without any single expensive step.

Second, the Hold wrapper. The step tactic runs simp on all hypotheses in the context. After processing a function like to_bytes, you end up with postconditions involving expensive terms. Any subsequent step call times out because simp tries to reduce these. The fix: wrap the expensive hypothesis in an opaque Hold definition before calling step. Simp can't see through it. Then afterwards, recover the original proposition via definitional equality with `change`. It's zero proof obligation — purely a performance trick. This pattern is universally useful for anyone doing Lean verification at scale.

---

### Slide 12 — Upstreaming

I want to emphasise the upstreaming culture. This isn't just about our project — we contribute back to the ecosystem.

We've merged six PRs into Aeneas: better docstring generation, showing Rust visibility in Lean output, a version flag, replacing custom implementations with upstream equivalents, and a fix for the progress tactic. We've filed six issues against Charon and eight or more against Aeneas — things like exponential slowdown with typenum, wrapping shift bugs, codegen issues. Each one we try to isolate into a minimal reproducer so the Aeneas and Charon maintainers can act on it efficiently.

Going forward, we're planning to upstream our Lean models of Rust core types and operations, so other verification projects can reuse them. The Lean community has a strong upstreaming culture — definitions go to Mathlib, tool improvements go to Aeneas — and we want to be part of that.

---

### Slide 13 — Conclusions

To wrap up. The toolchain works. We've verified 84 percent of curve25519-dalek's functions — all the core arithmetic, point operations, compression and decompression.

The key lessons: plan for iterator elimination from the start. Know that trait boundaries are the extraction frontier. And proof performance at this scale requires real engineering — bridge lemmas, the Hold wrapper, careful heartbeat tuning. These aren't theoretical concerns, they're daily realities.

What's next: completing the remaining 20 proofs, resolving those 5 sorry statements where Lean's kernel can't handle 78-digit numbers, and moving on to additional crates in the libsignal dependency tree.

Thank you.

---

### Slide 14 — Thank you

[Questions]
