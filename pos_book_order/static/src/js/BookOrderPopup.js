/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class BookOrderPopup extends Component {
//Popup to create and save a POS booked order with pickup or delivery details.
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
    checkMethod(){
    /**
    * Toggles delivery and pickup UI sections based on
    * the selected delivery method and updates address.
    */
        if (this.delivery.el.checked){
            this.Method_deliver.el.classList.remove('d-none')
            this.Method_pickup.el.classList.add('d-none')
            this.delivery_address = this.address
        }else{
            this.Method_deliver.el.classList.add('d-none')
            this.Method_pickup.el.classList.remove('d-none')
        }
    }
    async confirm() {
    /**
    * Confirms the order by collecting order, customer,
    * delivery/pickup, and product details, then creates
    * a booked order and refreshes the booked orders screen.
    */
        const pickup_date = this.pickup_date.el.value;
        const delivery_date = this.delivery_date.el.value;
        const order_note = this.order_note.el.value;
        const partner = this.props.partner.id;
        const address = this.delivery_address?.el?.value || "";
        const phone = this.props.partner.phone;

        // --- Fix for date_order (string or Date object) ---
        let jsDate = this.order.date_order;
        let date;
        if (jsDate instanceof Date) {
            // Format manually if it's a Date object
            date =
                jsDate.getFullYear() + "-" +
                String(jsDate.getMonth() + 1).padStart(2, "0") + "-" +
                String(jsDate.getDate()).padStart(2, "0") + " " +
                String(jsDate.getHours()).padStart(2, "0") + ":" +
                String(jsDate.getMinutes()).padStart(2, "0") + ":" +
                String(jsDate.getSeconds()).padStart(2, "0");
        } else if (typeof jsDate === "string") {
            date = jsDate.replace("T", " ").split(".")[0];
        } else {
            date = new Date().toISOString().slice(0, 19).replace("T", " ");
        }

        const line = this.order.lines;
        const pos_order = this.order.uid;

        const price_list = this.order.pricelist_id || false;

        let rawLines = this.order?.get ? this.order.get("lines") : this.order.lines;
        const priceData = this.order._prices?.original || {};
        const baseLines = priceData.baseLines || [];

        const product = {
            product_id: [],
            qty: [],
            price: [],
            tax_ids: []
        };

        for (const line of baseLines) {
            const pid   = line.product_id?.id;
            const qty   = line.quantity;
            const unit  = line.price_unit;

            const subtotal_excl = line.tax_details?.raw_total_excluded || (unit * qty);
            const subtotal_incl = line.tax_details?.raw_total_included || subtotal_excl;
            const tax_ids = line.tax_ids?.map(t => t.id) || [];


            product.product_id.push(pid);
            product.qty.push(qty);
            product.price.push(unit);
            product.tax_ids.push(tax_ids);

        }


        const self = this;

        // --- Create Booked Order ---
        await this.orm
            .call(
                "book.order",
                "create_booked_order",
                [partner, phone, address, date, price_list, product, order_note, pickup_date, delivery_date, pos_order],
                {}
            )
            .then(function (book_order) {
                self.order.booking_ref_id = book_order;
            });

        // --- Refresh Booked Orders Screen ---
        await this.orm
            .call("book.order", "all_orders", [], {})
            .then(function (result) {
                self.pos.navigate("BookedOrdersScreen", {
                    data: result,
                    new_order: true,
                });
            });

        this.props.close();
    }
}