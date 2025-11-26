/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";


patch(PosStore.prototype, {
    async setDiscountFromUI(line, val) {
       var a = line.set_discount(val) || '';
       if (a && a.title == "Discount Not Possible"){
            this.dialog.add(AlertDialog, {
                    title: _t("Discount Not Possible"),
                    body: _t("You cannot apply discount above the discount limit."),
                });
           }
       }
})
