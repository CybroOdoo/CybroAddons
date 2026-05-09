/** @odoo-module **/
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { MassEditPopup } from "./pos_mass_edit_popup";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";

export class MassEditButton extends Component {
    static template = "all_in_one_pos_kit.MassEditButton";
    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }
    async onClick() {
        var order = this.pos.get_order();
        var order_line = order.get_orderlines();

        if (!order_line.length) {
            this.dialog.add(AlertDialog, {
                title: _t("Order is Empty"),
                body: _t("You need to add product."),
            });
        }
        else {
            await makeAwaitable(this.dialog, MassEditPopup, {
                title: _t("Edit Order Line"),
                body: order_line
            });
        }
    }
}

patch(ControlButtons, {
    components: { ...ControlButtons.components, MassEditButton },
});
