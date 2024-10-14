import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";

patch(PaymentScreen.prototype, {
           setup() {
               super.setup(...arguments);
               this.totalPayment = this.currentOrder.getTotalDue();
               this.tipValue = 0;
           },
           async CustomTipButton(){
                // It is used to update the tip to payment
                var custom_tip_percentage = this.env.services.pos.config.custom_tip_percentage
                if(custom_tip_percentage){
                    this.env.services.pos.tips = true;
                    this.env.services.pos.custom_tip = custom_tip_percentage
                    var tipPercent = parseInt(custom_tip_percentage) /100
                    var cust_tip = this.totalPayment * tipPercent
                    let value = cust_tip === 0 && change > 0 ? change : cust_tip;
                    this.tipValue += value
                    this.dialog.add(NumberPopup, {
                        title: cust_tip ? _t("Change Tip") : _t("Add Tip"),
                        startingValue: this.env.utils.formatCurrency(value, false),
                        formatDisplayedValue: (x) => `${this.pos.currency.symbol} ${x}`,
                        getPayload: async (value) => {
                            await this.pos.set_tip(parseFloat(this.tipValue ?? ""));
                            this.totalPayment += parseFloat(value)
                        },
                    });
                    }
           },
           get Tips() {
           // calculates the tips and return to the template
                var custom_tip_percentage = this.env.services.pos.config.custom_tip_percentage
                if(custom_tip_percentage){
                    this.env.services.pos.tips = true;
                    this.env.services.pos.custom_tip = custom_tip_percentage
                    }
                else{
                    this.env.services.pos.tips = false;
                }
                return {
                        tip:custom_tip_percentage,
                        tip_enable:this.env.services.pos.tips ,
                };
           },
});