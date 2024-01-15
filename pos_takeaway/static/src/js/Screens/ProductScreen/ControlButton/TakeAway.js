/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { useRef } from "@odoo/owl";

export class TakeAwayButton extends ProductScreen {
    static template = "TakeAwayButton";
    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.TakeAway = useRef("TakeAway");
    }
    async onClick() {
        const SelectedOrder = this.pos.get_order();
        if (SelectedOrder.is_empty()) {
            return alert ('Please add product!!');
        }else{
            this.TakeAway.el.className = "control-button customer-button btn rounded-0 fw-bolder text-truncate btn-primary";
            SelectedOrder.is_take_away = true;
            SelectedOrder.generate_token = true;
            SelectedOrder.token_number = await this.orm.call('pos.order', 'token_generate', [SelectedOrder.uid])
        }
    }
}
// Register the component
ProductScreen.addControlButton({
    component: TakeAwayButton,
    condition: function () {
        return this.pos.config.module_pos_restaurant && this.pos.config.is_pos_takeaway;
    },
});
