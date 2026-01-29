/** @odoo-module **/
/*
 * This file is used to register a new screen for Booked orders.
 */
import Registries from 'point_of_sale.Registries';
import TicketScreen from 'point_of_sale.TicketScreen';
import {useListener} from "@web/core/utils/hooks";

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
    const newOrder = this.env.pos.add_new_order();
    this.env.pos.set_order(newOrder);
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
    var order = this.env.pos.get('orders').models.find((order) => order.uid == uid);
    var partner_id = data.partner_id
    order.is_booked = true
    order.booked_data = data
    order.booking_ref_id = data.id
    this.env.pos.set_order(order);

    this.showScreen('ProductScreen');
}
}
BookedOrdersScreen.template = 'BookedOrdersScreen';
Registries.Component.add(BookedOrdersScreen);