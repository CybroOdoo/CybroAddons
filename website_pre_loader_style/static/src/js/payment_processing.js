/** @odoo-module **/

import paymentPostProcessing from '@payment/js/post_processing';
import { _t } from '@web/core/l10n/translation';

paymentPostProcessing.include({
    async start() {
        this.call('ui', 'block', {
            'message': _t("We are processing your payment, please wait ..."),
        });
        return this._super(...arguments);
    },
});
