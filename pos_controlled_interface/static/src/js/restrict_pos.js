/**
 * Created by cybrosys on 12/12/17.
 */
odoo.define('pos_controlled_interface', function (require) {
    "use strict";
    // Restrict the sales persons in the interface
    var screens = require('point_of_sale.screens');
    screens.NumpadWidget.include({
        clickChangeMode: function(event) {
            var newMode = event.currentTarget.attributes['data-mode'].nodeValue;
            if (newMode =='discount' && this.pos.config.control_discount){
                return 0;
            }
            else if(newMode =='price' && this.pos.config.control_price){
                return 0;
            }
            else{
                return this.state.changeMode(newMode);
            }

            }
    })

});
