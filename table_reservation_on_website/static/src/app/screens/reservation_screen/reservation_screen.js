/** @odoo-module */

import { registry } from "@web/core/registry";
import { Component, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { EditBookingPopup } from "@table_reservation_on_website/app/booking_popup/editBookingPopup";
import { createBookingPopup } from "@table_reservation_on_website/app/booking_popup/createBookingPopup";

export class ReservationsScreen extends Component {
    static template = "table_reservation_on_website.ReservationsScreen";
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.pos = usePos();
        this.popup = useService("popup");
        this.state = useState({
            bookings: [],
            booking_id: [],
        });
        onWillStart(async () => {
            await this.getReservationList()
        })
    }
    // Displays reservations in reservation screen
    async getReservationList() {
        var data = await this.orm.call('table.reservation', 'table_reservations', [[]])
        this.state.bookings = data
        const posTables = this.env.services.pos.tables_by_id
    }
    // Get reservation details
    get bookingList() {
        return this.state.bookings || []
    }
    // Popup for editing reservations
    async onClickEdit(data) {
        const { confirmed, payload } = await this.popup.add(EditBookingPopup, {
            title: _t("Edit Reservation"),
            data
        });
    }
    // For cancelling Reservations
    async onClickCancel(data){
        var res_id = data['id']
        await this.orm.call('table.reservation', 'cancel_reservations', [data['id']])
        if (data.order_name){
            var order = this.pos.orders.find(order => order.name === data.order_name);
            if(order){
                this.pos.removeOrder(order);
            }
        }
        location.reload()
    }
    // Popup for creating reservations
    async createBooking() {
        const { confirmed, payload } = await this.popup.add(createBookingPopup, {
            title: _t("Reserve Table"),
        });
    }
}
registry.category("pos_screens").add("ReservationsScreen", ReservationsScreen);
