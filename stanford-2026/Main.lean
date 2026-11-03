module

public import VersoSlides
import Slides

open VersoSlides

public def main : IO UInt32 :=
  slidesMain (config := { theme := "white" }) (doc := %doc Slides)
