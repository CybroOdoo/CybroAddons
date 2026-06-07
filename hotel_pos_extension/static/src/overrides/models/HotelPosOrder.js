/** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
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

    serializeForORM(opts = {}) {
        const data = super.serializeForORM(opts);
        // many2one to an unloaded model is skipped by generic serializer.
        data.booking_id = this.getBookingId();
        return data;
    },
});
