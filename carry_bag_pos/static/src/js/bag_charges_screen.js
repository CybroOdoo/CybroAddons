odoo.define('carry_bag_pos.bag_charges_screen', function(require) {
  'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class CategoryScreen extends PosComponent {
        /**
            *Override PosComponent
        */
    click(event) {
        // Get current target
        var self = this;
        var product_id = parseInt(event.currentTarget.dataset['productId'])
        self.env.pos.get_order().add_product(self.env.pos.db.product_by_id[product_id]);
        // Add products to the pos order line
        this.showScreen("ProductScreen");
        }
        back() {
             this.showScreen("ProductScreen");
        }
    }
    CategoryScreen.template = 'CategoryScreen';
    Registries.Component.add(CategoryScreen);
    return CategoryScreen;
});
