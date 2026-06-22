/** @odoo-module **/
import { registry } from "@web/core/registry";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";

class BookedOrdersScreen extends TicketScreen {
    static template = "pos_book_order.BookedOrdersScreen";
    static props = {
        data: Object, // Add this if 'data' is expected
        new_order: Boolean, // Add this if 'new_order' is expected
    };
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
    }
    /**
     * Navigates back to the Product Screen.
     */
    back() {
        this.pos.showScreen('ProductScreen');
    }
    /**
     * Completes the order process and redirects
     * the user to the Product Screen with a new order.
     */
    orderDone() {
        // on clicking the back button it will redirected Product screen
        this.pos.add_new_order()
        this.pos.showScreen('ProductScreen');
    }
    /**
     * Confirms a booked order.
     * This function calls the backend method `action_confirm`
     * to convert a booked order into a POS order.
     * After confirmation, the order is loaded into the POS
     * so the user can proceed with payment.
     */
    async _Confirm(ev) {
        var self = this
        var data = ev
        var uid = await this.orm.call('book.order', 'action_confirm', [data.id], {})
        var order = self.pos.get_order()
        order.is_booked = true;
        ev.pos_reference=order.pos_reference
        order.booked_data = ev
        this.pos.showScreen('ProductScreen');
    }
}
registry.category("pos_screens").add("BookedOrdersScreen", BookedOrdersScreen);