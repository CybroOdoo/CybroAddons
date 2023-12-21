odoo.define('pos_access_right_hr.NumpadWidget', function(require) {
 'use strict';

    const NumpadWidget = require('point_of_sale.NumpadWidget');
    const Registries = require('point_of_sale.Registries');
    /**
    Extend the file NumpadWidget to disable or enable the working of
    NumpadWidget
    **/
    const NumpadWidgetAccessRight= NumpadWidget => class extends NumpadWidget {
        /**
        * Disable the Qty button on the POS
        */
        get disable_quantity() {
            if(this.env.pos.get_cashier()){
                if(this.env.pos.get_cashier().disable_qty == false){
                    return false;
                }
                else{ return true;}
            }
            else{ return false;}
        }
        /**
        * Disable the Price button on the POS
        */
        get disable_price() {
            if(this.env.pos.get_cashier()){
                if(this.env.pos.get_cashier().disable_price == false){
                    return false;
                }
                else{ return true;}
            }
            else{ return false;}
        }
        /**
        * Disable the Discount button on the POS
        */
        get disable_discount() {
            if(this.env.pos.get_cashier()){
                if(this.env.pos.get_cashier().disable_discount == false){
                    return false;
                }
                else{ return true;}
            }
            else{ return false;}
        }
        /**
        * Disable the +/- button on the POS
        */
        get plusminus() {
            if(this.env.pos.get_cashier()){
                if(this.env.pos.get_cashier().disable_plus_minus == false){
                    return false;
                }
                else{ return true;}
            }
            else{ return false;}
        }
        /**
        * Disable the number pad on the POS
        */
        get numpad() {
            if(this.env.pos.get_cashier()){
                if(this.env.pos.get_cashier().disable_numpad == false){
                    return false;
                }
                else{ return true;}
            }
            else{ return false;}
        }
        /**
        * Disable the back button on the POS
        */
        get remove_button() {
            if(this.env.pos.get_cashier()){
                if(this.env.pos.get_cashier().disable_remove_button == false){
                    return false;
                }
                else{ return true;}
            }
            else{ return false;}
        }
    };
    Registries.Component.extend(NumpadWidget, NumpadWidgetAccessRight);
    return NumpadWidget;
});
