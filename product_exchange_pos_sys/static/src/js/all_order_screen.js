/** @odoo-module */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ExchangeOrder } from "./exchange_order";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
export class CustomOrderScreen extends Component {
//Extended the PosComponent to add button popup function
    static template = "CustomOrderScreen"
    setup() {
    //Setup method called when the component is mounted.
        super.setup();
        this.orm = useService("orm");
        this.pos = usePos()
        this.state = useState({
            order: this.props.orders,
            data: this.props.data,
            pos: this.env.pos
        });

        this.popup = useService("popup");
    }
    back() {
        this.env.services.pos.showScreen('ProductScreen');
    }
   async _onClickOrder(order, pos) {
   //Function to show popup to show exchange product it that pos order.
        let value =    await this.orm.call("pos.order.line", "get_product_details",[order.lines]);
        await this.popup.add(ExchangeOrder,  {
            'order_line': value,
            'pos': pos,
            'order_id': order.id
        });

    }
   };
registry.category("pos_screens").add("CustomOrderScreen", CustomOrderScreen);
