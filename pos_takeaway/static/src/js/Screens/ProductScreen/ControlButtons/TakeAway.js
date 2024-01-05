/** @odoo-module **/
const { useListener } = require("@web/core/utils/hooks");
const Dialog = require('web.Dialog');
import { _t } from 'web.core';
import PosComponent from 'point_of_sale.PosComponent';
import Registries from 'point_of_sale.Registries';
import ProductScreen from 'point_of_sale.ProductScreen';
import { Gui } from 'point_of_sale.Gui';

//    Extending the PosComponent to enable the takeaway for the order.
    class SendToTakeaway extends PosComponent {
        setup() {
            useListener('click', this.onClick);
        }
		onClick() {
            var selectedOrder = this.env.pos.get_order();
            selectedOrder.initialize_validation_date();
            if(selectedOrder.is_empty()){
                return alert ('Please add product!!');
            }else{
                const sendButton = document.getElementById('takeaway_button_id');
                sendButton.className = "control-button highlight";
                selectedOrder.is_take_way = true;
                const takeawaySetting = this.props;
            }
		}
    };
SendToTakeaway.template = 'SendToTakeaway';
ProductScreen.addControlButton({
 component: SendToTakeaway,
 condition: function() {
            return this.env.pos.config.module_pos_restaurant && this.env.pos.res_config_settings[this.env.pos.res_config_settings.length -1]['takeaway'];
        },
});
Registries.Component.add(SendToTakeaway);
return SendToTakeaway;
