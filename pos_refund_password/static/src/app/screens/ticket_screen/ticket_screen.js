/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";

// Keep original method reference
const _super_onDoRefund = TicketScreen.prototype.onDoRefund;

patch(TicketScreen.prototype, {

    async onDoRefund() {
        try {
            let globalPassword = null;

            // Fetch global refund password
            try {
                globalPassword = await this.pos.data.call(
                    "pos.config",
                    "fetch_global_refund_security",
                    []
                );
            } catch (rpcError) {
                console.warn("Could not fetch global refund password RPC:", rpcError);
            }
            
            const globalRefundPassword = globalPassword || null;
            // POS-specific password
            const posRefundPassword = this.pos.config?.refund_security || null;

            // Check if any password exists
            if (globalRefundPassword || posRefundPassword) {

                const inputPassword = await makeAwaitable(this.dialog, NumberPopup, {
                    title: _t("Confirm ?"),
                    placeholder: _t("Enter Password"),
                    isValid: (v) => true,
                    formatDisplayedValue: (input) => (input ? input.replace(/./g, "•") : ""),
                });

                // If popup closed
                if (!inputPassword) {
                    return;
                }

                // Allow if matches either password
                if (
                    inputPassword == globalRefundPassword ||
                    inputPassword == posRefundPassword
                ) {
                    await _super_onDoRefund.apply(this, arguments);
                } else {
                    this.env.services.notification.add(_t("Incorrect Password"), {
                        type: "warning",
                        title: _t("Error"),
                    });
                }

            } else {
                // No password configured
                await _super_onDoRefund.apply(this, arguments);
            }

        } catch (error) {
            console.error("Error during refund password validation:", error);
            this.env.services.notification.add(
                _t("An error occurred while validating refund password."),
                {
                    type: "danger",
                    title: _t("Error"),
                }
            );
        }
    },
});