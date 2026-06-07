/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class HotelRoomPopup extends Component {
    static template = "hotel_pos_extension.HotelRoomPopup";
    static components = { Dialog };

    setup() {
        this.state = useState({
            selectedBooking: this.props.bookings[0] || null,
        });
    }

    onBookingChange(ev) {
        const bookingId = parseInt(ev.target.value);
        this.state.selectedBooking = this.props.bookings.find(b => b.id === bookingId);
    }

    confirm() {
        this.props.getPayload(this.state.selectedBooking);
        this.props.close();
    }

    cancel() {
        this.props.close();
    }
}
