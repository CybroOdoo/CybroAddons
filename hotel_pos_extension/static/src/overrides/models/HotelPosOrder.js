/** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosPayment } from "@point_of_sale/app/models/pos_payment";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    initState() {
        super.initState(...arguments);
        // Stored in uiState so it survives IndexedDB and is easy to show in the UI.
        this.uiState.roomName ??= "";
        this.uiState.bookingId ??= false;
    },

    setBooking(booking) {
        if (!booking) {
            this.uiState.roomName = "";
            this.uiState.bookingId = false;
            return;
        }

        // room.booking is not a model loaded in POS, keep id in uiState and push to ORM payload.
        this.uiState.bookingId = booking.id;
        this.uiState.roomName = booking.name || "";
    },

    getBookingId() {
        return this.uiState.bookingId || false;
    },

    serialize() {
        const data = super.serialize(...arguments);
        // many2one to an unloaded model is skipped by generic serializer — add it manually.
        data.booking_id = this.getBookingId();
        return data;
    },

    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(baseUrl, headerData);
        // Attach roomName so the receipt template can display it.
        result.roomName = this.uiState.roomName || "";
        return result;
    },
});

patch(PosPayment.prototype, {
    export_for_printing() {
        const result = super.export_for_printing();
        // Expose is_hotel_charge so the receipt template can check it per payment line.
        result.is_hotel_charge = this.payment_method_id?.is_hotel_charge || false;
        return result;
    },
});
