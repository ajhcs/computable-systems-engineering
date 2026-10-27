package Maintenance1995 {
 private import ScalarValues::*;
 private import ISQBase::DurationValue;
 private import SI::h;
 part def CrewCode;
 action def TimedTask {
  attribute startOffset : DurationValue;
  attribute duration : DurationValue;
 }
 part Schedule {
  doc /* NASA 1995 Fig B-10; source offsets graphically read at 0.1 h. Assignments do not assert four actual qualified workers. */
  part A2 : CrewCode;
  part B1 : CrewCode;
  part C1 : CrewCode;
  part D1 : CrewCode;
  perform action C01 : TimedTask {
   doc /* Inspect compressor belt; source task .01. */
   attribute :>> startOffset = 0 [h];
   attribute :>> duration = 0.3 [h];
  }
  allocation allocC01 allocate C01 to A2;
  perform action C02 : TimedTask {
   doc /* Lubricate blowdown pump; source task .02. */
   attribute :>> startOffset = 0.1 [h];
   attribute :>> duration = 0.2 [h];
  }
  allocation allocC02 allocate C02 to B1;
  perform action C03 : TimedTask {
   doc /* Check mounting bolts; source task .03. */
   attribute :>> startOffset = 0.3 [h];
   attribute :>> duration = 0.1 [h];
  }
  allocation allocC03 allocate C03 to B1;
  perform action C04 : TimedTask {
   doc /* Clean breather cap; source task .04. */
   attribute :>> startOffset = 0.4 [h];
   attribute :>> duration = 0.1 [h];
  }
  allocation allocC04 allocate C04 to B1;
  perform action C05 : TimedTask {
   doc /* Clean food strainer; source task .05. */
   attribute :>> startOffset = 0 [h];
   attribute :>> duration = 0.5 [h];
  }
  allocation allocC05 allocate C05 to C1;
  perform action C06 : TimedTask {
   doc /* Replace oil; source task .06. */
   attribute :>> startOffset = 0.5 [h];
   attribute :>> duration = 0.2 [h];
  }
  allocation allocC06 allocate C06 to B1;
  perform action C07 : TimedTask {
   doc /* Replace filter; source task .07. */
   attribute :>> startOffset = 0.5 [h];
   attribute :>> duration = 0.4 [h];
  }
  allocation allocC07 allocate C07 to C1;
  perform action C08 : TimedTask {
   doc /* Replace V-drive belt; source task .08. */
   attribute :>> startOffset = 0 [h];
   attribute :>> duration = 0.9 [h];
  }
  allocation allocC08 allocate C08 to D1;
  perform action C09 : TimedTask {
   doc /* Clean & inspect control panel; source task .09. */
   attribute :>> startOffset = 0.9 [h];
   attribute :>> duration = 0.1 [h];
  }
  allocation allocC09 allocate C09 to C1;
  perform action C10 : TimedTask {
   doc /* Install new diaphragms; source task .10. */
   attribute :>> startOffset = 0.3 [h];
   attribute :>> duration = 0.7 [h];
  }
  allocation allocC10 allocate C10 to A2;
  perform action C11 : TimedTask {
   doc /* Clean controls; source task .11. */
   attribute :>> startOffset = 0.9 [h];
   attribute :>> duration = 0.1 [h];
  }
  allocation allocC11 allocate C11 to B1;
 }
}
