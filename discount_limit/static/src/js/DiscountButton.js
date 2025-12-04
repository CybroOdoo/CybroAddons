/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";

patch(ControlButtons.prototype, {
     async clickDiscount() {
        /**Add Popup error when Cashier is not allowed for apply Discount Limit**/
        var self=this;
        if (this.pos.cashier.has_pos_discount_control===true){
            return this.notification.add(_t("You must be granted access to apply discount."), {
                    title: _t("Discount Restricted"),
                    type: "danger",
                });
        }
        else
        {
            this.dialog.add(NumberPopup, {
                title: _t("Discount Percentage"),
                startingValue: this.pos.config.discount_pc,
                getPayload: (num) => {
                    const val = Math.max(
                        0,
                        Math.min(100, this.env.utils.parseValidFloat(num.toString()))
                    );
                    this.apply_discount(val);
                },
            });
        }
     },
});
