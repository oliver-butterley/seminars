import Lake

open Lake DSL

require «verso-slides» from git
  "https://github.com/leanprover/verso-slides.git" @ "6d40babad888bba1f83bf82badd680612d3899ac"

package «stanford-2026» where
  version := v!"0.1.0"

lean_lib Slides

@[default_target] lean_exe slides where root := `Main
