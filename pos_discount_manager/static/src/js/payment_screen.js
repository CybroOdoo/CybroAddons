/* global Sha1 */
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
//Patching PaymentScreen
patch(PaymentScreen.prototype, {
    async _finalizeValidation() {
        var order = this.pos.get_order();
        var orderlines = this.currentOrder.get_orderlines()
        var employee_dis = this.pos.get_cashier()['limited_discount'];
        var employee_name = this.pos.get_cashier()['name']
        var manager = this.pos.get_cashier()
        var flag = 1;
        if (employee_dis != 0) {
            orderlines.forEach((order) => {
                if(order.discount > employee_dis)
                flag = 0;
            });
        }
        if (flag != 1) {
            this.dialog.add(NumberPopup, {
                title: _t(employee_name + ', your discount is over the limit. \n Manager pin for Approval'),
                getPayload: async (num) => {
                    if (manager.parent_id){
                        var output = this.pos.models["hr.employee"].filter((obj) => obj.id === manager.parent_id.id );
                     if (Sha1.hash(num) == output[0]._pin) {
                          await super._finalizeValidation(...arguments);
                     } else {
                        this.notification.add(_t("Manager Restricted your discount"), {
                        type: "danger",
                            title: _t(employee_name + ", Your Manager pin is incorrect."),
                        });
                     }
                    } else {
                       this.notification.add(_t("Manager/Pin not set"), {
                        type: "danger",
                            title: _t(employee_name + ", Manager/Pin not set."),
                        });
                    }
                },
            });
        } else {
            await super._finalizeValidation(...arguments);
        }
    }
});
