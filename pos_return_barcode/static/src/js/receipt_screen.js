// Part of Odoo. See LICENSE file for full copyright and licensing details.
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import  { useState } from "@odoo/owl";
import { onWillStart } from "@odoo/owl";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { usePos } from "@point_of_sale/app/store/pos_hook";


patch(OrderReceipt.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.pos = usePos();
        this.order = this.pos.get_order()
        this.state = useState({
            barcode :''
        });
        onWillStart(() => {
            this.fetch_barcode()
        });
    },

    async fetch_barcode() {
        const is_barcode = await this.orm.call("ir.config_parameter", "get_param", ["pos_return_barcode.receipt_barcode"])
         const order = await this.orm.searchRead("pos.order",
                       [["id", "=", this.order.id]],
                       ['barcode']);
         if(is_barcode){
        order.forEach(element =>{
            this.state.barcode = element.barcode
            this.order.barcode = element.barcode

        })
        }
    }
});