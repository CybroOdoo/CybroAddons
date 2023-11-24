odoo.define('pos_discount_manager.ValidateManager', function(require) {
    'use strict';

  const Registries = require('point_of_sale.Registries');
  const PaymentScreen = require('point_of_sale.PaymentScreen');
  var session = require('web.session');

     const ValidateManagers = (PaymentScreen) =>
        class extends PaymentScreen {
                /**
                *Override the validate button to approve discount limit
                */
            async _finalizeValidation() {
                var order = this.env.pos.get_order();
                var orderlines = this.currentOrder.get_orderlines()
                var employee_dis = this.env.pos.get_cashier()['limited_discount'];
                var employee_name = this.env.pos.get_cashier()['name']
                var flag = 1;
                 orderlines.forEach((order) => {
                   if(order.discount > employee_dis)
                   flag = 0;
                 });
                 if (flag != 1) {
                 const {confirmed,payload} = await this.showPopup('NumberPopup', {
                            title: this.env._t(employee_name + ', your discount is over the limit. \n Manager pin for Approval'),
                            isPassword: true
                        });
                        if(confirmed){
                         var output = this.env.pos.employees.filter((obj) => obj.role == 'manager' && obj.user_id == session.uid);
                         var pin = output[0].pin
                         if (Sha1.hash(payload) == pin) {
                            this.showScreen(this.nextScreen);
                            }
                            else {
                                this.showPopup('ErrorPopup', {
                                    title: this.env._t(" Manager Restricted your discount"),
                                    body: this.env._t(employee_name + ", Your Manager pin is incorrect."),

                                });
                                return false;
                            }
                        }
                        else {
                            return false;
                        }
                        }
                        this.currentOrder.finalized = true;
                        this.showScreen(this.nextScreen);
                        super._finalizeValidation();
                        // If we succeeded in syncing the current order, and
                       // there are still other orders that are left unsynced,
                      // we ask the user if he is willing to wait and sync them.
            }
        }
     Registries.Component.extend(PaymentScreen, ValidateManagers);
     return ValidateManagers;
});
