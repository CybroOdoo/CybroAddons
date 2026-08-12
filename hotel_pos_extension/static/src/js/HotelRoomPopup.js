/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useState } from "@odoo/owl";

export class HotelRoomPopup extends AbstractAwaitablePopup {
    static template = "hotel_pos_extension.HotelRoomPopup";
    static props = {
        title: String,
        bookings: Array,
        close: Function,
        id: { type: Number, optional: true },
        resolve: { type: Function, optional: true },
        zIndex: { type: Number, optional: true },
        cancelKey: { type: String, optional: true },
        confirmKey: { type: String, optional: true },
    };

    setup() {
        super.setup();
        this.state = useState({
            selectedBooking: this.props.bookings[0] || null,
        });
    }

    onBookingChange(ev) {
        const bookingId = parseInt(ev.target.value);
        this.state.selectedBooking = this.props.bookings.find(b => b.id === bookingId);
    }

    async getPayload() {
        return this.state.selectedBooking;
    }
}
