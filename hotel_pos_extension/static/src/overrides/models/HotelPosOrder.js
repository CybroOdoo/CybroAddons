/** @odoo-module */

import { Order, Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    initialize(attributes, options = {}) {
        super.initialize(...arguments);
        // Initialize hotel booking fields in uiState
        this.uiState.roomName = this.uiState.roomName ?? "";
        this.uiState.bookingId = this.uiState.bookingId ?? false;
    },

    setBooking(booking) {
        if (!booking) {
            this.uiState.roomName = "";
            this.uiState.bookingId = false;
            return;
        }
        // room.booking is not loaded in POS, store id in uiState
        this.uiState.bookingId = booking.id;
        this.uiState.roomName = booking.name || "";
    },

    getBookingId() {
        return this.uiState.bookingId || false;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.uiState.roomName = json.room_name || "";
        this.uiState.bookingId = json.booking_id || false;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.booking_id = this.getBookingId();
        json.room_name = this.uiState.roomName || "";
        return json;
    },

    export_for_printing() {
        const json = super.export_for_printing(...arguments);
        json.room_name = this.uiState.roomName || "";
        json.booking_id = this.getBookingId();
        return json;
    },
});

patch(Payment.prototype, {
    export_for_printing() {
        const json = super.export_for_printing(...arguments);
        json.is_hotel_charge = this.payment_method.is_hotel_charge || false;
        return json;
    },
});


