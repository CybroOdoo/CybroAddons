import { patch } from "@web/core/utils/patch";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { TextInputPopup } from "@point_of_sale/app/components/popups/text_input_popup/text_input_popup";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
    },
    async clickPaymentReference() {
        const line = this.currentOrder.getSelectedPaymentline();
        if (!line) {
            this.notification.add(_t("Please choose a payment method first."), {
                type: "warning",
            });
            return;
        }
        const reference = await makeAwaitable(this.dialog, TextInputPopup, {
            title: _t("Payment Reference"),
            startingValue: line.user_payment_reference || "",
            placeholder: _t("eg: PREF16"),
        });
        if (reference !== undefined && reference !== null) {
            line.user_payment_reference = reference;
        }
    },
});
