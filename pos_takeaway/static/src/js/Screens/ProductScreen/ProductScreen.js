odoo.define('pos_takeaway.ProductScreen', function(require) {
    'use strict';
    const ProductScreen = require('point_of_sale.ProductScreen')
    const Registries = require('point_of_sale.Registries');
// Extending ProductScreen to add the button for Takeaway
    const TakeawayProductScreen = ProductScreen =>
        class extends ProductScreen {
            mounted() {
                var order = this.env.pos.get_order();
                var takeaway = order.is_take_way;
                if(takeaway){
                    const takeawayButton = document.getElementById('takeaway_button_id');
                    takeawayButton.className = "control-button highlight";
                }
            }
        }
    Registries.Component.extend(ProductScreen, TakeawayProductScreen);
    return ProductScreen;
});