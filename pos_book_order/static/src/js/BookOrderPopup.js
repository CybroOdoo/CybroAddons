/** @odoo-module **/
/*
 * This file is used to register the a new popup to book pickup and deliver orders.
 */
import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
const rpc = require('web.rpc');
import {Gui} from 'point_of_sale.Gui';

class BookOrderPopup extends AbstractAwaitablePopup {
    setup() {
        super.setup()
        this.order = this.env.pos.get_order();

    }
    async onConfirm() {
        // On clicking confirm button of popup a new book order with draft stage will created from the backend
        var pickup_date = this.el.querySelector('#pickup_date').value;
        var delivery_date = this.el.querySelector('#deliver_date').value;
        var order_note = this.el.querySelector('.order_note').value;
        var partner = this.order.get_client().id;
        var address = this.el.querySelector('#delivery_address').value;
        var phone = this.el.querySelector('#phone').value;
        var date = this.order.creation_date;
        var line = this.order.get_orderlines();
        var price_list = this.order.pricelist.id;
        var uid = this.order.uid;
        var product = {
            'product_id': [],
            'qty': [],
            'price':[]
        };
        for (var i = 0; i < line.length; i++) {
            product['product_id'].push(line[i].product.id)
            product['qty'].push(line[i].quantity)
            product['price'].push(line[i].price)
        };
        var self = this
        await this.rpc({
        //  this call for is creating a book order in the backend based on the value in popup
            model: 'book.order',
            method: 'create_booked_order',
            args: [partner, phone, address, date, price_list, product, order_note, pickup_date, delivery_date,uid]
        }).then(function(book_order) {
            self.order.booking_ref_id=book_order
        })
        await this.rpc({
            model: 'book.order',
            method: 'all_orders',
        }).then(function(result) {
            self.showScreen('BookedOrdersScreen', {
                data: result,
                new_order: true,
            });
        })
        this.cancel();
    }
}
BookOrderPopup.template = 'BookOrderPopup';
Registries.Component.add(BookOrderPopup);