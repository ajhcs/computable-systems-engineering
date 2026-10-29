package ConfigurationLibrary {
    part def Sensor;
    part def Accessory;
    part def HistoricalSensor;
    part def AlternativeSystem;
    part def BaseSystem {
        part sensor : Sensor;
    }
    part def SelectedSystem :> BaseSystem {
        part accessory : Accessory;
    }
}
