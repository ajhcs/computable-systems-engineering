package BookingCase {
    private import ScalarValues::Boolean;
    doc /* Original synthetic black-box context and selected available-slot path. Internals are not selected. No implementation evidence or engineer acceptance is supplied. */
    item def BookRequest;
    item def ReservationReceipt;
    part def Client {
        out item bookingRequest : BookRequest;
        in item reservationReceipt : ReservationReceipt;
    }
    part def BookingDesk {
        in item bookingRequest : BookRequest;
        out item reservationReceipt : ReservationReceipt;
        in attribute request : Boolean;
        out attribute recorded : Boolean;
    }
    part client : Client;
    part desk : BookingDesk;
    flow bookRequestFlow of BookRequest from client.bookingRequest to desk.bookingRequest;
    flow reservationReceiptFlow of ReservationReceipt from desk.reservationReceipt to client.reservationReceipt;
    concern <N_BOOKING> BookingAccess {
        doc /* Proposed synthetic need: clients need access to booking services. This concern is not a measured obligation or accepted engineer intent. */
    }
    action def BookAvailableSlot {
        first start;
        then action receiveRequest;
        then action checkAvailability;
        then action recordReservation;
        then done;
    }
    use case <UC_AVAILABLE> BookAvailableSlotCase {
        subject unit = desk;
        actor user = client;
        doc /* Selected available-slot path: receiveRequest, checkAvailability, recordReservation, then done. Succession specifies order only. No unavailable branch, duration, or physical-component allocation is selected. */
    }
    doc cseClock /* CSE-CLOCK/2.0
    period 1 second */
    requirement <R_RECEIPT> TimelyRecord {
        doc /* Proposed teaching obligation only; no engineer acceptance exists. It constrains Boolean recording, without asserting receipt delivery or equating Boolean signals with item flows. */
        doc cseSource /* CSE-SOURCE/2.0
        SYN-EVAL-01 */
        subject unit = desk;
        require constraint responseTime {
            doc cse /* CSE-REQ/2.0
            Upon unit.request = true, unit shall within 2 seconds
            satisfy unit.recorded = true. */
        }
    }
}