/** @odoo-module **/
import { _t } from '@web/core/l10n/translation';
import { patch } from '@web/core/utils/patch';
import { PaymentForm } from '@payment/interactions/payment_form';

patch(PaymentForm.prototype, {
    /**
     * @override
     */
    async submitForm(ev) {
        const extraInfoForm = document.querySelector('#extra_info_form');
        if (extraInfoForm) {
            extraInfoForm.submit();
        }
        return super.submitForm(...arguments);
    },
});

