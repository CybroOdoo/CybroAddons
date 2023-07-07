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
     // on clicking the back button it will redirected Product screen
        this.showScreen('ProductScreen');
    }
    _Confirm(ev) {
        // On clicking confirm button on  each order a order will create with corresponding partner and products,user can do the payment
        var self = this
        var data = ev.detail
        this.env.pos.add_new_order();
        for (var i of data.products) {
            var product = self.env.pos.db.get_product_by_id(i['id'])
            var qty = i['qty']
            this.env.pos.get_order().add_product(product, {
                quantity: qty,
                 price: i['price']
            })
        }
        var partner_id = data.partner_id
        this.env.pos.get_order().set_client(this.env.pos.db.get_partner_by_id(partner_id));
        this.env.pos.get_order().is_booked = true
        this.env.pos.get_order().booked_data = data
        this.showScreen('ProductScreen');
    }
}
BookedOrdersScreen.template = 'BookedOrdersScreen';
Registries.Component.add(BookedOrdersScreen);