// Synthetic composition interaction fixture. No real equipment claims.
package Composition {
    part def Sensor;
    part def Base {
        part <SENSOR> sensor [2] : Sensor;
    }
    part def Assembly :> Base;
    part current : Assembly;
}
