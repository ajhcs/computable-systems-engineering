package ReturnRecording {
    private import ScalarValues::String;
    doc cseClock /*CSE-CLOCK/2.0
    period 1 second
    */
    concern <N_RECORD> TraceableReturn {
        doc /*Synthetic question: retain an item-specific condition record promptly.
        The proposed time bound needs engineer review for a real project.*/
    }
    part def ReturnDesk {
        in event occurrence returnAccepted { attribute correlationId : String; }
        out event occurrence conditionRecorded { attribute correlationId : String; }
    }
    part desk : ReturnDesk;
    action def InspectReturn {
        doc /*A documentary function. Its activation, physical inspection and
        termination are not executed or inferred by the trace monitor.*/
    }
    requirement <R_RECORD> RecordEachAcceptedReturn {
        doc cseSource /*CSE-SOURCE/2.0
        SYN-RETURN-1
        */
        subject unit = desk;
        require constraint recordingTime {
            doc cse /*CSE-EVENT/2.0
            Each unit.returnAccepted shall within 4 minutes have
            unit.conditionRecorded with matching correlationId.
            */
        }
    }
}
