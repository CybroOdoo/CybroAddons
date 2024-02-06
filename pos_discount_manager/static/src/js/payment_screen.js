/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
//if the employee give discount beyond his limit then the manager needs to approve
patch(PaymentScreen.prototype, {
                /**
                *Override the validate button to approve discount limit
                */
            async _finalizeValidation() {
                var order = this.pos.get_order();
                var orderlines = this.currentOrder.get_orderlines()
                var employee_dis = this.pos.get_cashier()['limited_discount'];
                var employee_name = this.pos.get_cashier()['name']
                var flag = 1;
                 orderlines.forEach((order) => {
                   if(order.discount > employee_dis)
                   flag = 0;
                 });
                 if (flag != 1) {
                 const {confirmed,payload} = await this.popup.add(NumberPopup, {
                            title: _t(employee_name + ', your discount is over the limit. \n Manager pin for Approval'),
                            isPassword: true
                        });
                        if(confirmed){
                         var output = this.pos.employees.filter((obj) => obj.role == 'manager' && obj.user_id == session.uid);
                         var pin = output[0].pin
                         if (Sha1.hash(payload) == pin) {
                           this.pos.showScreen(this.nextScreen);
                            }
                            else {
                                this.popup.add(ErrorPopup, {
                                    title: _t(" Manager Restricted your discount"),
                                    body: _t(employee_name + ", Your Manager pin is incorrect."),

                                });
                                return false;
                            }
                        }
                        else {
                            return false;
                        }
                        }
                        this.currentOrder.finalized = true;
                        this.pos.showScreen(this.nextScreen);
                       await super._finalizeValidation(...arguments);
            }
        });
