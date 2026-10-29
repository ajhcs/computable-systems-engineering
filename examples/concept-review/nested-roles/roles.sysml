package NestedRoles {
    part def Sensor;
    part def PreciseSensor :> Sensor;
    part def Machine {
        part sensor : Sensor;
        part auxiliaries : Sensor [0..*];
    }
    part def SelectedMachine :> Machine {
        part sensor : PreciseSensor redefines Machine::sensor;
        part spare : Sensor subsets auxiliaries;
        part disabled : Sensor [0..0];
    }
    part def OtherMachine { part sensor : Sensor; }
    part machine : SelectedMachine;
    part other : OtherMachine;
    action def Acquire;
    concern Need;
}
