package SharedAck {
    private import ScalarValues::Boolean;

    part def Controller {
        in attribute request : Boolean;
        out attribute acknowledged : Boolean;
    }
}
