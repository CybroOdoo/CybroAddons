/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { TransferPopup } from "@stock_transfer_in_pos/app/utils/input_popups/transfer_popup";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";

patch(ControlButtons.prototype, {
        setup() {
        super.setup();
        // Why not `this.orm = useService("orm");` ?
        // Because in the `onClick` method, the first action call will potentially open the `new layout action wizard`
        // closing the current dialog. Once closed, the succeeding actions will be terminated because of the protection
        // made by calling `useService`. We want to continue with the full logic of the `onClick` method even if the
        // dialog is closed.
        this.orm = this.env.services.orm;

    },
        async clickDiscount1() {
        // This will show a popup to transfer stock with selected products and customer
        var self = this

        // Error popup
        if (this.pos.getOrder().lines.length === 0)
        {
            this.dialog.add(WarningDialog, {
                        title: _t("Odoo Warning"),
                        message: _t("Please Select at least one product for transferring"),
                        });
        }
        else
        {
            await this.orm.call(
                "pos.config", "get_stock_transfer_list", [], {}
            ).then(function(result) {
                self.dialog.add(TransferPopup, {
                data: result,
                title: _t("Create Transfer"),
                });
            });
        }
    }
});