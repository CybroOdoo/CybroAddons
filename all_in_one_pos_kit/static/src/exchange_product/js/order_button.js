/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { _t } from "@web/core/l10n/translation";
import {ErrorPopup} from "@point_of_sale/app/errors/popups/error_popup";
import {ExchangeOrder} from "./exchange_order";

class OrderLineALLButton extends ProductScreen {
    static template = "OrderLineALL";
    setup() {
        super.setup();
    }
    async onClick() {
//      Order line button Onclick()
        await this.pos.showScreen('CustomOrderScreen', {
                orders: this.env.services.pos.pos_orders,
                pos: this.env.services.pos
            });
    }
}
ProductScreen.addControlButton({
    component: OrderLineALLButton,
});
