# v12 compact anchor h-instantiated grind

Promoted from `solvers/solo_official/drafts/2026-05-12/d5`.

Remote gates:

- `dev_fast`: `1895A / 105R / 0E`, +34 accepted vs v11.
- `dev_main`: `9442A / 558R / 0E`, +149 accepted vs v11.
- `test_locked`: `47031A / 2969R / 0E`, +700 accepted vs v11, false accepted unchanged, LLM 0.

The new compiler emits compact anchor h-instantiations for single-variable-LHS true goals and lets `grind` close them.
