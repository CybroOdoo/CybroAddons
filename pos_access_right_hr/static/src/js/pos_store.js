/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PosStore.prototype, {
    async pay() {
        if (this.cashier?.disable_payment) {
            this.dialog.add(AlertDialog, {
                title: _t("Access Denied"),
                body: _t("You are not allowed to make payments."),
            });
            return;
        }
        await super.pay(...arguments);
    }
});
