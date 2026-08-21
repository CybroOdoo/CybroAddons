/** @odoo-module **/
import { registry } from "@web/core/registry";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";

class BookedOrdersScreen extends TicketScreen {
/**
* Custom POS screen used to display booked orders and
* convert them into active POS orders for payment.
* Extends TicketScreen and integrates with the backend
* `book.order` model for confirmation.
*/
    static template = "pos_book_order.BookedOrdersScreen";
    static props = {
        data: Object,
        new_order: Boolean,
    };
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        if (!this.pos) {
        }
    }
    back() {
        // on clicking the back button it will redirected Product screen
        this.pos.navigate('ProductScreen');
    }
    orderDone() {
        // on clicking the back button it will redirected Product screen
        this.pos.addNewOrder();
        this.pos.navigate('ProductScreen');
    }
    async _Confirm(ev) {
        // On clicking confirm button on  each order a order will create with corresponding partner and products,user can do the payment
        var self = this
        var data = ev
        var uid = await this.orm.call('book.order', 'action_confirm', [data.id], {})
        var order = this.pos.selectedOrder
        order.is_booked = true;
        ev.pos_reference=order.pos_reference
        order.booked_data = ev
        this.pos.navigate('ProductScreen');

    }
}
registry.category("pos_pages").add("BookedOrdersScreen", {
    name: "BookedOrdersScreen",
    component: BookedOrdersScreen,
    route: `/pos/ui/${odoo.pos_config_id}/bookorder`,
    params: {},
});