# Signal Shot: end-to-end verification of Signal in Lean

*Project update, September 2026*

Signal Shot aims to prove, with machine-checked mathematics, that Signal messenger's cryptography does what it claims: both that the protocols have the relevant security properties and that these are faithfully implemented by the code. It launched in April 2026, organised by the Beneficial AI Foundation in close collaboration with the Lean FRO and engineers at Signal.

## The problem: gaps and coverage

Signal's protocols are among the best-analysed, yet two limits remain. The first is **gaps**: a protocol's design is proved secure in one set of tools \[1\] and its code checked in another \[2, 3\], with nothing formally connecting them; code can drift from design unnoticed. The second is **coverage**: until now, proofs demanded scarce experts and long hours, so much of the code and many newer protocols have none.

## The goal: one tool, full coverage

We are using one tool, Lean, for everything. The verification target is libsignal, the library inside every Signal client: about 45,000 lines of Rust plus its cryptographic dependencies. Its protocols start conversations, encrypt each message, hide the sender and run private groups. Translating the Rust code to Lean, we aim at three things:

1. **Code correctness:** the code never crashes and exactly matches its specification.  
2. **Protocol security:** messages stay confidential and authentic against precisely defined attackers.  
3. **The link:** the code faithfully implements the protocols proved secure.

The proofs will live with the code and run on every change. Beyond verifying this particular code, the aim is to improve the tools (all open source) until such proofs are routine.

## How it works

**Lean** \[5\] is an interactive theorem prover and a programming language. It brings *mathlib*, a library containing, among others, the mathematics that these proofs need, and automation that users can extend. **Aeneas** \[6\], created and maintained by Son Ho, translates Rust code in Lean so it can be reasoned about. In terms of protocol security, the attacker is any program interacting with the protocol and the theorem bounds its chance of breaking it. Implementation code and protocol are all in Lean so there are no manual links between tools. Specifications are carefully written by humans whilst AI drafts much of the proof work, but Lean checks every step, so nothing rests on trusting the AI.

## Where things stand

Code correctness is now routine: proofs for curve25519-dalek (an elliptic-curve cryptography library) are complete, and the new post-quantum code is nearing completion. Much effort goes into improving the tools themselves, so that such proofs become easy for everyone, not only for formal verification experts. Proving is now so much easier that choosing the right specifications takes most of the time. Protocol work has moved from exploration to formalising protocols and their security proofs at scale.

## Why now

Lean and AI-assisted proving have matured to the point where this work is feasible \[4\]. Signal's code is written with unusual care, but as AI-written code is trusted more widely, machine-checked specifications and proofs become the key safeguard. Completing this ambitious project will show a way of working that is increasingly essential, and push the tools to support it.

## References

1. K. Bhargavan, C. Jacomme, F. Kiefer, R. Schmidt. *Formal verification of the PQXDH post-quantum key agreement protocol for end-to-end secure messaging.* USENIX Security 2024\. [https\://www\.usenix.org/conference/usenixsecurity24/presentation/bhargavan](https://www.usenix.org/conference/usenixsecurity24/presentation/bhargavan)  
2. Signal. *Signal Protocol and Post-Quantum Ratchets.* 2025\. [https\://signal.org/blog/spqr/](https://signal.org/blog/spqr/)  
3. Cryspen. *Helping secure Signal's post-quantum transition.* 2025\. [https\://cryspen.com/post/signal-spqr-verification/](https://cryspen.com/post/signal-spqr-verification/)  
4. L. de Moura. *Signal Shot: The Platform Is Ready.* Blog post, 20 April 2026\. [https\://leodemoura.github.io/blog/2026-4-20-signal-shot-the-platform-is-ready/](https://leodemoura.github.io/blog/2026-4-20-signal-shot-the-platform-is-ready/)  
5. Lean. [https\://lean-lang.org/](https://lean-lang.org/)  
6. Aeneas. [https\://github.com/AeneasVerif/aeneas](https://github.com/AeneasVerif/aeneas)