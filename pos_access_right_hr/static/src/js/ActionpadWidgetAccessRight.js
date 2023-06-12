odoo.define('pos_access_right_hr.ActionPad_extension', function(require) {
  'use strict';
    const ActionpadWidget = require('point_of_sale.ActionpadWidget');
    const Registries = require('point_of_sale.Registries');
    const ActionpadWidgetAccessRight= ActionpadWidget => class extends ActionpadWidget {
    //To enable or disable buttons in the ActionpadWidget

     /**
     * Disable the customer selection button on the POS
     */
    get disable_customer() {
       if (this.env.pos.config.module_pos_hr) {
        const cashierId = this.env.pos.get_cashier().id;
        const sessionAccess = this.env.pos.session_access.find(access => access.id === cashierId);
        if (sessionAccess && sessionAccess.disable_customer) {
            self.$('#customer_disable').css({ "border": "1px solid #C9CCD2", "background-color": "#E0E2E6","color":"#666666" });
        }
        return sessionAccess ? sessionAccess.disable_customer : false;
    }
    else {return false;}
    }
     /**
     * Disable the customer selection button on the POS
     */
     get disable_payment() {
       if (this.env.pos.config.module_pos_hr) {
           const cashierId = this.env.pos.get_cashier().id;
           const sessionAccess = this.env.pos.session_access.find(access => access.id === cashierId);
           if (sessionAccess && sessionAccess.disable_payment) {
               self.$("#payment_disable").css({ "border": "1px solid #C9CCD2", "background-color": "#E0E2E6","color":"#666666" });
           }
           return sessionAccess ? sessionAccess.disable_payment : false;
       }
       else {return false;}
     }
  };
  Registries.Component.extend(ActionpadWidget, ActionpadWidgetAccessRight);
  return ActionpadWidget;
 });
