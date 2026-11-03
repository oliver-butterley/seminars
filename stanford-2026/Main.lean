module

public import VersoSlides
import Slides

open VersoSlides

public def main : IO UInt32 := do
  -- Read at run time (not `include_str`), so CSS edits apply without a Lean rebuild.
  let css ← IO.FS.readFile "custom.css"
  slidesMain
    (config := {
      theme := "white"
      slideNumber := true
      center := false
      extraCss := #[{ filename := "custom.css", contents := ⟨css⟩ }] })
    (doc := %doc Slides)
