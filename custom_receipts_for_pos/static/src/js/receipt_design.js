/** @odoo-module */
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { useState, Component, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(OrderReceipt.prototype, {
    setup(){
        super.setup();
            this.state = useState({
                template: true,
            })
        this.pos = useState(useService("pos"));
    },
    get templateProps() {
        return {
                data: this.props.data,
                order: this.pos.orders,
                receipt: this.pos.orders[0].export_for_printing(),
                orderlines:this.pos.orders[0].get_orderlines(),
                paymentlines:this.pos.orders[0].get_paymentlines()
        }
    },
    get templateComponent() {
        var mainRef = this
        return class extends Component {
            setup() {}
            static template = xml`${mainRef.pos.config.design_receipt}`
        }
    },
    get isTrue() {
        if (this.env.services.pos.config.is_custom_receipt == false) {
            return true
        }
        else {
            return false
        }
    }
});
