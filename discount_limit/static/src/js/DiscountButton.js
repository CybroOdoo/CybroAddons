/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { DiscountButton } from "@pos_discount/overrides/components/discount_button/discount_button";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
patch(DiscountButton.prototype, {
     async click() {
        /**Add Popup error when Cashier is not allowed for apply Discount Limit**/
        var self=this;
        if (this.pos.get_cashier().has_pos_discount_control===true){
            this.popup.add(ErrorPopup, {
                    title: _t("Discount Restricted"),
                    body: _t("You must be granted access to apply discount."),
                });
                return false;
        }
        else
        {
          var self = this;
            const { confirmed, payload } = await this.popup.add(NumberPopup,{
                title: _t('Discount Percentage'),
                startingValue: this.pos.config.discount_pc,
            });
              if (confirmed) {
                const val = Math.round(Math.max(0,Math.min(100,parseFloat(payload))));
                await self.apply_discount(val);
            }
        }
     },
});
