/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { _t } from "@web/core/l10n/translation";
import {ErrorPopup} from "@point_of_sale/app/errors/popups/error_popup";
import {MassEditPopup} from "./pos_mass_edit_popup";

class MassEditButton extends ProductScreen {
    static template = "SaleOrderButton";
    setup() {
        super.setup();
    }
    async onClick() {
//      Order line button Onclick()
        var order = this.pos.get_order();
        var order_line = order.get_orderlines();

        if (!order_line.length){
//      Popup if no product in pos order line
            await this.popup.add(ErrorPopup, {
                title: _t("Order is Empty"),
                body: _t("You need to add product."),
            });
        }
        else {
            const { confirmed } = await this.popup.add(MassEditPopup, {
                title: _t("Edit Order Line"),
                body: order_line
            });
        }
    }
}
ProductScreen.addControlButton({
    component: MassEditButton,
    position:['after','OrderlineCustomerNoteButton']
});
