/** @odoo-module */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ExchangeOrder } from "./exchange_order";

export class CustomOrderScreen extends Component { //Extended the PosComponent to add button popup function
    static template = "CustomOrdrScreen"
    setup() {
    //Setup method called when the component is mounted.
        super.setup();
        console.log('knnn',this.props)
        this.orm = useService("orm");
        this.pos = useService('pos')
        this.state = {
            order: this.props.orders,
            pos: this.env.pos
        };
        this.popup = useService("popup");
    }
    back() {
        this.env.services.pos.showScreen('ProductScreen');
    }
   async _onClickOrder(order, pos) {
   //Function to show popup to show exchange product it that pos order.
        console.log('ooo',this)
        if (order.exchange == true) {
            this.pos.showPopup('ErrorPopup', {
                title: 'Exchange order',
                body: 'Already created the Exchange order'
            });
        } else {
            let value =    await this.orm.call("pos.order.line", "get_product_details",[order.lines]);
            await this.popup.add(ExchangeOrder,  {
                'order_line': value,
                'pos': pos,
                'order_id': order.id
            });
        }
    }
    };
registry.category("pos_screens").add("CustomOrderScreen", CustomOrderScreen);
