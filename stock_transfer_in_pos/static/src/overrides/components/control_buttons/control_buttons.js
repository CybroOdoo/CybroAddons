import { _t } from "@web/core/l10n/translation";
import { TransferPopup } from "@stock_transfer_in_pos/app/utils/input_popups/transfer_popup";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";

patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.orm = this.env.services.orm;
    },

    async clickStockTransfer() {
        // Show a popup to transfer stock with selected products
        const order = this.pos.getOrder();
        const lines = order ? (order.getOrderlines ? order.getOrderlines() : order.lines) : [];

        if (!lines || lines.length === 0) {
            this.dialog.add(WarningDialog, {
                title: _t("Odoo Warning"),
                message: _t("Please select at least one product to transfer."),
            });
            return;
        }

        try {
            const result = await this.orm.call(
                "pos.config",
                "get_stock_transfer_list",
                [],
                {}
            );
            this.dialog.add(TransferPopup, {
                data: result,
                configId: this.pos.config.id,
                title: _t("Create Transfer"),
            });
        } catch (error) {
            this.dialog.add(WarningDialog, {
                title: _t("Error"),
                message: error.message || _t("Unable to fetch stock transfer configuration."),
            });
        }
    },
});