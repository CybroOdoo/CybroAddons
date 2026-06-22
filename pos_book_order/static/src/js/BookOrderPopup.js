/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Dialog } from "@web/core/dialog/dialog";

export class BookOrderPopup extends Component {
    static template = "pos_book_order.BookOrderPopup";
    static components = {
        Dialog
    };
    static props = {
        title: {
            type: String,
            optional: true
        },
        close: Function,
        partner: Object,
        order: Object,
    };
    static defaultProps = {
        confirmText: _t("Save"),
        cancelText: _t("Discard"),
        clearText: _t("Clear"),
        title: "",
        body: "",
    };
    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.pos = usePos();
        this.orm = useService("orm");
        this.order = this.pos.selectedOrder
        this.pickup_date = useRef("pickUpDate")
        this.order_note = useRef("orderNote")
        this.delivery_date = useRef("deliveryDate")
        this.pickup = useRef("pickup_radio")
        this.delivery = useRef("deliver_radio")
        this.Method_pickup = useRef("Method_pickup")
        this.Method_deliver = useRef("Method_deliver")
        this.address = useRef("delivery_address")
        this.delivery_address = false
    }
    /**
     * Handles switching between pickup and delivery methods.
     * Shows or hides corresponding UI sections depending
     * on the selected radio button.
     */
    checkMethod(){
        if (this.delivery.el.checked){
            this.Method_deliver.el.classList.remove('d-none')
            this.Method_pickup.el.classList.add('d-none')
            this.delivery_address = this.address
        }else{
            this.Method_deliver.el.classList.add('d-none')
            this.Method_pickup.el.classList.remove('d-none')
        }
    }
     /**
     * Creates a booked order record.
     * Collects order data including:
     * - customer details
     * - order lines
     * - pickup/delivery dates
     * - order notes
     * Sends the data to the backend method
     * `create_booked_order` to store the booking.
     * After saving, the booked orders screen is displayed.
     */
    async confirm() {
        var pickup_date = this.pickup_date.el.value;
        var delivery_date = this.delivery_date.el.value;
        var order_note = this.order_note.el.value;
        var partner = this.props.partner.id;
        var address = this.delivery_address?.el?.value || "";
        var phone = this.props.partner.phone;
        var date = this.order.date_order;
        var line = this.order.lines;
        var pos_order = this.order.uid;
        if (this.pickup.el.checked && !pickup_date) {
            this.dialog.add(AlertDialog, {
                title: _t("Validation Error"),
                body: _t("Pickup Date is required."),
            });
            return;
        }
        if (this.delivery.el.checked && !delivery_date) {
            this.dialog.add(AlertDialog, {
                title: _t("Validation Error"),
                body: _t("Delivery Date is required."),
                    });
            return;
        }
        if (this.delivery.el.checked && !address) {
            this.dialog.add(AlertDialog, {
                title: _t("Validation Error"),
                body: _t("Delivery Address is required."),
                    });
            return;
        }
        if (this.order.pricelist_id) {
            var price_list = this.order.pricelist_id;
        } else {
            var price_list = false;
        }
        var product = {
            'product_id': [],
            'qty': [],
            'price': []
        };
        for (var i = 0; i < line.length; i++) {
            product['product_id'].push(line[i].product_id.id)
            product['qty'].push(line[i].qty)
            product['price'].push(line[i].price_subtotal)
        };
        var self = this
        await this.orm.call(
            "book.order", "create_booked_order", [partner, phone, address, date, price_list, product, order_note, pickup_date, delivery_date, pos_order], {}
        ).then(function(book_order) {
            self.order.booking_ref_id = book_order
        })
        await this.orm.call(
            "book.order", "all_orders", [], {}
        ).then(function(result) {
            self.pos.showScreen('BookedOrdersScreen', {
                data: result,
                new_order: true
            });
        })
        this.props.close();
    }
}