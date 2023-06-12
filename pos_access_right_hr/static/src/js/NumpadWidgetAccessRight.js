odoo.define('pos_access_right_hr.CustomOrdrScreen', function(require) {
 'use strict';
    const NumpadWidget = require('point_of_sale.NumpadWidget');
    const Registries = require('point_of_sale.Registries');
    const NumpadWidgetAccessRight= NumpadWidget => class extends NumpadWidget {
    //To enable or disable buttons in the NumpadWidget

     /**
     * Disable the Qty button on the POS
     */
     get disable_quantity() {
        if (this.env.pos.config.module_pos_hr) {
            const cashierId = this.env.pos.get_cashier().id;
            const sessionAccess = this.env.pos.session_access.find(access => access.id === cashierId);
            return sessionAccess ? sessionAccess.disable_qty : false;
        }
        else { return false;}
     }

     /**
     * Disable the Price button on the POS
     */
     get disable_price() {
        if (this.env.pos.config.module_pos_hr) {
            const cashierId = this.env.pos.get_cashier().id;
            const sessionAccess = this.env.pos.session_access.find(access => access.id === cashierId);
            return sessionAccess ? sessionAccess.disable_price : false;
        }
        else { return false;}
    }

     /**
     * Disable the Discount button on the POS
     */
    get disable_discount() {
       if (this.env.pos.config.module_pos_hr) {
            const cashierId = this.env.pos.get_cashier().id;
            const sessionAccess = this.env.pos.session_access.find(access => access.id === cashierId);
            return sessionAccess ? sessionAccess.disable_discount : false;
        }
        else { return false;}
    }

     /**
     * Disable the +/- button on the POS
     */
    get plusminus() {
       if (this.env.pos.config.module_pos_hr) {
            const cashierId = this.env.pos.get_cashier().id;
            const sessionAccess = this.env.pos.session_access.find(access => access.id === cashierId);
            return sessionAccess ? sessionAccess.disable_plus_minus : false;
        }
        else { return false;}
    }

     /**
     * Disable the number pad on the POS
     */
    get numpad() {
        if (this.env.pos.config.module_pos_hr) {
            const cashierId = this.env.pos.get_cashier().id;
            const sessionAccess = this.env.pos.session_access.find(access => access.id === cashierId);
            return sessionAccess ? sessionAccess.disable_numpad : false;
        }
        else { return false;}
    }

    /**
     * Disable the back button on the POS
     */
    get remove_button() {
       if (this.env.pos.config.module_pos_hr) {
            const cashierId = this.env.pos.get_cashier().id;
            const sessionAccess = this.env.pos.session_access.find(access => access.id === cashierId);
            return sessionAccess ? sessionAccess.disable_remove_button : false;
        }
        else { return false;}
    }
    };
    Registries.Component.extend(NumpadWidget, NumpadWidgetAccessRight);
    return NumpadWidget;
 });
