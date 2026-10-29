package LinkContext {
    private import LinkLibrary::*;
    part current : System;
    part historical : System;
    ref part enterprise : Receiver;
    ref part secondReceiver : Receiver;
    connection dataLink connect current.sensor.output to enterprise.input;
}
