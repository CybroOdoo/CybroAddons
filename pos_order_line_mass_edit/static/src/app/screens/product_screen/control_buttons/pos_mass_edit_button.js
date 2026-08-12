/** @odoo-module */

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { MassEditPopup } from "@pos_order_line_mass_edit/app/utils/mass_edit_popup/mass_edit_popup";

//Edit Order Line button
patch(ControlButtons.prototype, {
    async EditOrderLine() {
        var order = this.pos.getOrder();
        var order_line = order.getOrderlines();
        if (!order_line.length){
            this.dialog.add(AlertDialog, {
                title: _t("Order is Empty"),
                body: _t(
                    "You need to add at least one product."
                ),
            });
        } else {
            this.dialog.add(MassEditPopup, {
                'body': order_line
            });
        }
    }
})