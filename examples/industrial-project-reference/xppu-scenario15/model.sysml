// Source-derived structural projection; GPL-3.0, x-PPU/Models at c3aedf66f3e9695e6a7751ae62d17c64b1bc373c
// Only seven direct composite PPU module roles. State/action/ISA88/OMAC semantics remain unconverted in the original.
package XPPUScenario15Selected {
  // Source Block _P1xSIBHVEeaen93uATCTQQ
  part def Stack {}
  // Source Block _uUK40BHWEeaE9dGXaplL2g
  part def Crane {}
  // Source Block _-GUi8BHWEeaE9dGXaplL2g
  part def Stamp {}
  // Source Block _RehDsBH4EeaIeI6F5gdpJg
  part def LargeSortingConveyor {}
  // Source Block _5QIQAOcBEeayP7zJxSzVpQ
  part def PicAlphaConveyor {}
  // Source Block _-ESikOcBEeayP7zJxSzVpQ
  part def SmallSortingConveyor {}
  // Source Block _EV7fwOcCEeayP7zJxSzVpQ
  part def RefillConveyor {}
  // Source Block _2ub-IBHQEeaen93uATCTQQ
  part def PPU {
    // Source property _K9YqEhHZEeaIeI6F5gdpJg; composite; association _K9YDABHZEeaIeI6F5gdpJg
    part stack : Stack [1..1];
    // Source property _MFHHIhHZEeaIeI6F5gdpJg; composite; association _MFGgEBHZEeaIeI6F5gdpJg
    part crane : Crane [1..1];
    // Source property _N1dDYxHZEeaIeI6F5gdpJg; composite; association _N1dDYBHZEeaIeI6F5gdpJg
    part stamp : Stamp [1..1];
    // Source property _cpnDIxH4EeaIeI6F5gdpJg; composite; association _cpnDIBH4EeaIeI6F5gdpJg
    part largeSortingConveyor : LargeSortingConveyor [1..1];
    // Source property _NypR0OcCEeayP7zJxSzVpQ; composite; association _NykZUOcCEeayP7zJxSzVpQ
    part picAlphaConveyor : PicAlphaConveyor [1..1];
    // Source property _QzKcgucCEeayP7zJxSzVpQ; composite; association _QzJOYOcCEeayP7zJxSzVpQ
    part smallSortingConveyor : SmallSortingConveyor [1..1];
    // Source property _lWsgEOcEEeayP7zJxSzVpQ; composite; association _lWqD0OcEEeayP7zJxSzVpQ
    part refillConveyor : RefillConveyor [1..1];
  }
}
