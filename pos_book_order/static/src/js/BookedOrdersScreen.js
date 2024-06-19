/** @odoo-module **/
/*
 * This file is used to register a new screen for Booked orders.
 */
import Registries from 'point_of_sale.Registries';
import TicketScreen from 'point_of_sale.TicketScreen';
import {useListener} from "@web/core/utils/hooks";
import { useService } from "@web/core/utils/hooks";


class BookedOrdersScreen extends TicketScreen {
    setup() {
        super.setup();
        useListener('click-confirm', this._Confirm);
    }
    back() {
        this.showScreen('ProductScreen');
    }
    orderDone() {
     // on clicking the back button it will redirected Product screen
    this.env.pos.add_new_order()
    this.showScreen('ProductScreen');
    }
    async _Confirm(ev) {
    // On clicking confirm button on  each order a order will create with corresponding partner and products,user can do the payment
    var self = this
    var data = ev.detail
    var uid = await this.rpc({
                    model: 'book.order',
                    method: 'action_confirm',
                    args: [data.id]
                })
    var order = this.env.pos.orders.find((order) => order.uid == uid);
    var partner_id = data.partner_id
    this.env.pos.selectedOrder=order
    this.env.pos.selectedOrder.is_booked = true
    this.env.pos.selectedOrder.booked_data = data
    this.env.pos.selectedOrder.booking_ref_id = data.id
    this.showScreen('ProductScreen');
}
}
BookedOrdersScreen.template = 'BookedOrdersScreen';
Registries.Component.add(BookedOrdersScreen);