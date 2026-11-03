package NativeHandoff {
    private import ScalarValues::Boolean;
    doc /* Synthetic explicit correspondence; native behavior is not executed. */
    part def Person;
    part def DeskData {
        in attribute request : Boolean;
        out attribute ready : Boolean;
        out attribute result : Boolean;
        out attribute enabled : Boolean;
    }
    part clerk : Person;
    part desk : DeskData;
    action def Prepare;
    action def Complete;
    action def Handle;
    action def Routine;
    action def PrepareStep;
    action def CompleteStep;
}
