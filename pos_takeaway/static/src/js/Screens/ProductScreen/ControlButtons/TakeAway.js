odoo.define('pos_takeaway.SendToTakeaway', function(require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const models = require("point_of_sale.models");
    models.load_models({
        model: 'res.config.settings',
        fields: ['takeaway'],
        loaded: function(self, settings){
        if(settings.length){
            var index = settings.length-1
            self.takeaway = settings[index].takeaway;
            }
        },
    });
//    Extending the PosComponent to enable the takeaway for the order.
    class SendToTakeaway extends PosComponent {
        constructor() {
            super(...arguments);
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
            }
		}
    };
    SendToTakeaway.template = 'SendToTakeaway';
//    Adds the TakeAway button on ProductScreen
    ProductScreen.addControlButton({
        component: SendToTakeaway,
        condition: function() {
            return this.env.pos.config.module_pos_restaurant && this.env.pos.takeaway;
        },
    });
    Registries.Component.add(SendToTakeaway);
    return SendToTakeaway;
});