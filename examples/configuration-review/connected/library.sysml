package LinkLibrary {
    port def Data;
    part def Sensor {
        port output : Data;
    }
    part def InheritedSensor :> Sensor;
    part def System {
        part sensor : Sensor;
    }
    part def Receiver {
        port input : Data;
    }
}
