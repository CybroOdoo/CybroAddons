/** @odoo-module **/
/*
 * This file is used to register a new screen for Booked orders.
 */
import { registry } from "@web/core/registry";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";

class BookedOrdersScreen extends TicketScreen {
    static template = "pos_book_order.BookedOrdersScreen";
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
    }
    back() {
     // on clicking the back button it will redirected Product screen
        this.pos.showScreen('ProductScreen');
    }
    async _Confirm(ev) {
        // On clicking confirm button on  each order a order will create with corresponding partner and products,user can do the payment
        var self = this
        var data = ev
        await  this.orm.call('book.order', 'action_confirm',[data.id],{})
        var order=this.pos.add_new_order();
        for (var i of data.products) {
            var product = self.pos.db.get_product_by_id(i['id'])
            var qty = i['qty']
            order.add_product(product, {
                quantity: qty,
                price: i['price']
            })
        }
        var partner_id = data.partner_id
        order.set_partner(this.pos.db.get_partner_by_id(partner_id));
        this.pos.selectedOrder.is_booked = true
        this.pos.selectedOrder.booked_data = data
        this.pos.selectedOrder.booking_ref_id = data.id
        this.pos.showScreen('ProductScreen');
    }
}
registry.category("pos_screens").add("BookedOrdersScreen", BookedOrdersScreen);
