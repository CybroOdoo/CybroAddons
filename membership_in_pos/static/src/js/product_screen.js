/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { useService } from "@web/core/utils/hooks";

patch(PosStore.prototype, {
    async pay() {
        const current_order = this.get_order();
        const partner = current_order.get_partner();

        if (!partner) {
            this.dialog.add(AlertDialog, {
                title: _t("Customer"),
                body: _t("You Must Select a Customer"),
            });
            return;
        }

        const hasInvalidLot = current_order.get_orderlines().some(
            (line) =>
                line.get_product().tracking !== "none" &&
                !line.has_valid_product_lot()
        );

        if (
            hasInvalidLot &&
            (this.env.services.pos.pickingType.use_create_lots ||
                this.env.services.pos.pickingType.use_existing_lots)
        ) {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Some Serial/Lot Numbers are Missing"),
                body: _t(
                    "You are trying to sell products with serial/lot numbers, but some of them are not set.\nWould you like to proceed anyway?"
                ),
                confirm: () => {
                    this._proceedToPayment();
                },
                cancel: () => {

                },
            });
        } else {
            this._proceedToPayment();
        }
    },

    _proceedToPayment() {
        this.env.services.pos.mobile_pane = "right";
        this.env.services.pos.showScreen("PaymentScreen", {
            orderUuid: this.selectedOrderUuid,
        });
        super.pay();
    },
});