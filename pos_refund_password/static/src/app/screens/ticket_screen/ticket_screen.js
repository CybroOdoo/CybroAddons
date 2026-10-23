import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";

patch(TicketScreen.prototype, {
    async onDoRefund() {
        if (!this.pos.config?.has_refund_password) {
            return await super.onDoRefund(...arguments);
        }

        const inputPassword = await makeAwaitable(this.dialog, NumberPopup, {
            title: _t("Confirm Password"),
            placeholder: _t("Enter Password"),
            isValid: (input) => Boolean(input),
            formatDisplayedValue: (input) => (input ? input.replace(/./g, "•") : ""),
        });

        if (!inputPassword) {
            return;
        }

        const isValid = await this.pos.data.call(
            "pos.config",
            "verify_refund_password",
            [[this.pos.config.id], inputPassword]
        );

        if (isValid) {
            await super.onDoRefund(...arguments);
        } else {
            this.env.services.notification.add(_t("Incorrect Password"), {
                type: "warning",
                title: _t("Error"),
            });
        }
    },
});