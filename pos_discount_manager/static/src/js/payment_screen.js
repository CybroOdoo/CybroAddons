/* global Sha1 */
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

/**
 * Patching PaymentScreen to add custom validation for discount limits.
 */
patch(PaymentScreen.prototype, {
    /**
     * Validates the POS order and checks for discount limits.
     * If a cashier provides a discount that exceeds their allowed limit,
     * it prompts for a manager's PIN for approval.
     *
     * @param {boolean} isForceValidate - Indicates whether the validation is forced.
     * @returns {Promise<void>}
     */
    async validateOrder(isForceValidate) {
        const cashier = this.pos?.getCashier();
        if (!cashier || !this.currentOrder) {
            return await super.validateOrder(...arguments);
        }

        const discountLimit = cashier.limited_discount || 0;
        const orderlines = this.currentOrder.getOrderlines() || [];
        const isDiscountOverLimit = discountLimit !== 0 && 
            orderlines.some((line) => (line.discount || 0) > discountLimit);

        if (!isDiscountOverLimit) {
            return await super.validateOrder(...arguments);
        }

        this.dialog.add(NumberPopup, {
            title: _t((cashier.name || 'Cashier') + ', your discount exceeds the limit of ' + discountLimit + '%. \n Manager pin for Approval'),
            formatDisplayedValue: (x) => x.replace(/./g, "•"),
            getPayload: async (num) => {
                const parentId = cashier.parent_id?.id || cashier.parent_id;
                const employees = this.pos.models?.["hr.employee"] || [];
                const manager = parentId && employees.find((e) => e.id === parentId);

                if (!manager || !manager._pin) {
                    return this.notification.add(_t("Manager/Pin not set"), {
                        type: "danger",
                        title: _t((cashier.name || 'Cashier') + ", Manager/Pin not set."),
                    });
                }

                if (!num || Sha1.hash(num) !== manager._pin) {
                    return this.notification.add(_t("Manager Restricted your discount"), {
                        type: "danger",
                        title: _t((cashier.name || 'Cashier') + ", Your Manager pin is incorrect."),
                    });
                }

                await super.validateOrder(...arguments);
            },
        });
    }
});
