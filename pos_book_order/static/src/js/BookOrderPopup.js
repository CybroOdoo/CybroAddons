/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


export class BookOrderPopup extends AbstractAwaitablePopup {
    static template = "pos_book_order.BookOrderPopup";
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
        this.pickup_time = useRef("pickUpTime")
        this.order_note = useRef("orderNote")
        this.delivery_date = useRef("deliveryDate")
        this.delivery_time = useRef("deliveryTime")
        this.pickup = useRef("pickup_radio")
        this.delivery = useRef("deliver_radio")
        this.Method_pickup = useRef("Method_pickup")
        this.Method_deliver = useRef("Method_deliver")
    }

    showHide(){
        if(this.pickup.el.checked){
            this.Method_pickup.el.style.display='block'
            this.Method_deliver.el.style.display='none'
        }
        if(this.delivery.el.checked){
            this.Method_pickup.el.style.display='none'
            this.Method_deliver.el.style.display='block'
        }
    }

    async confirm() {
        var pickup_date = this.pickup_date.el.value;
        var pickup_time = this.pickup_time.el.value || "00:00";
        var delivery_date = this.delivery_date.el.value;
        var delivery_time = this.delivery_time.el.value || "00:00";
        var order_note = this.order_note.el.value;
        var partner = this.order.partner.id;
        var address = this.order.partner.address;
        var phone = this.order.partner.phone;
        var date = this.order.date_order;
        var line = this.order.orderlines;
        var pos_order = this.order.uid;
        if(this.order.pricelist){
            var price_list = this.order.pricelist.id;
        }
        else{
            var price_list = false;
        }
        var product = {
            'product_id': [],
            'qty': [],
            'price': []
        };
        for (var i = 0; i < line.length; i++) {
            product['product_id'].push(line[i].product.id)
            product['qty'].push(line[i].quantity)
            product['price'].push(line[i].price)
        };
        var self = this
        await this.orm.call(
            "book.order", "create_booked_order",
            [partner, phone, address, date, price_list, product, order_note, pickup_date, pickup_time, delivery_date, delivery_time, pos_order], {}  // NEW: delivery_time added
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
        this.cancel();
    }
}