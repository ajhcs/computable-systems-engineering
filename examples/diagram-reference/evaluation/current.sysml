package BookingScenario {
    doc /* Original synthetic teaching case, revision 1.
           System boundary: desk. Client is external; internals are unselected.
           R_RECEIPT is proposed, without engineer acceptance or implementation evidence. */

    item def BookRequest;
    item def ReservationReceipt;

    part def Client {
        out item bookRequest : BookRequest;
        in item reservationReceipt : ReservationReceipt;
    }

    part def BookingDesk {
        in item bookRequest : BookRequest;
        out item reservationReceipt : ReservationReceipt;
        in attribute request : Boolean;
        out attribute recorded : Boolean;
    }

    part client : Client;
    part desk : BookingDesk;

    flow F_REQUEST of BookRequest
        from client.bookRequest to desk.bookRequest;
    flow F_RECEIPT of ReservationReceipt
        from desk.reservationReceipt to client.reservationReceipt;

    concern C_BOOKING {
        doc /* Teaching concern: understand how an external booking request
               leads to a recorded reservation and a returned receipt. */
    }

    action availableSlotPath {
        doc /* Selected available-slot path only. Narrative ordering does not
               define executable guards or effects. No physical allocation is selected. */
        action receiveRequest;
        action checkAvailability;
        action recordReservation;
        first start then receiveRequest;
        then checkAvailability;
        then recordReservation;
        then done;
    }

    use case UC_BOOK {
        subject system : BookingDesk = desk;
        actor requester : Client = client;
        doc /* Available-slot booking: requester sends BookRequest to system;
               the selected path receives the request, checks availability,
               records the reservation, and completes. System returns
               ReservationReceipt to requester. Receipt timing relative to
               individual actions is not further specified. */
        include action booking : availableSlotPath;
    }

    requirement R_RECEIPT {
        subject unit : BookingDesk = desk;
        in attribute request : Boolean = unit.request;
        out attribute recorded : Boolean = unit.recorded;
        attribute cseClock : String = "1 s";
        attribute cseSource : String = "SYN-EVAL-01";
        doc /* Proposed teaching obligation.
               CSE-REQ/2.0: Upon unit.request = true, unit shall within 2 seconds satisfy unit.recorded = true. */
    }
}