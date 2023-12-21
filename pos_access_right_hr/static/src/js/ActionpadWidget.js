odoo.define('pos_access_right_hr.ActionPad_extension', function(require) {
  'use strict';
    const ActionpadWidget = require('point_of_sale.ActionpadWidget');
    const Registries = require('point_of_sale.Registries');
    /**
    Extend the file ActionpadWidget to enable or disable buttons in the
    ActionpadWidget
    **/
    const ActionpadWidgetAccessRight= ActionpadWidget => class extends ActionpadWidget {
        /**
        * Disable the customer selection button on the POS
        */
        get disable_customer() {
            if(this.env.pos.get_cashier()){
                if(this.env.pos.get_cashier().disable_customer == false){
                    self.$('#customer_disable').css({ "border": "1px solid #bfbfbf", "background-color": "#e2e2e2","color":"#555555" });
                    return false;
                }
                else{
                    self.$('#customer_disable').css({ "border": "1px solid #C9CCD2", "background-color": "#c7c7c7","color":"#a5a1a1" });
                    return true;
                }
            }
            else{
                self.$('#customer_disable').css({ "border": "1px solid #bfbfbf", "background-color": "#e2e2e2","color":"#555555" });
                return false;
            }
        }
        /**
        * Disable the payment button on the POS
        */
        get disable_payment() {
            if(this.env.pos.get_cashier()){
                if(this.env.pos.get_cashier().disable_payment == false){
                    self.$('#payment_disable').css({ "border": "1px solid #bfbfbf", "background-color": "#e2e2e2","color":"#555555" });
                    return false;
                }
                else{
                    self.$('#payment_disable').css({ "border": "1px solid #C9CCD2", "background-color": "#c7c7c7","color":"#a5a1a1" });
                    return true;
                }
            }
            else{
                self.$('#payment_disable').css({ "border": "1px solid #bfbfbf", "background-color": "#e2e2e2","color":"#555555" });
                return false;
            }
        }
    };
    Registries.Component.extend(ActionpadWidget, ActionpadWidgetAccessRight);
    return ActionpadWidget;
});
