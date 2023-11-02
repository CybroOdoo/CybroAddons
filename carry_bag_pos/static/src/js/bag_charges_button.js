odoo.define('carry_bag_pos.bag_charges.button', function(require) {
'use strict';
  const PosComponent = require('point_of_sale.PosComponent');
  const ProductScreen = require('point_of_sale.ProductScreen');
  const { useListener } = require("@web/core/utils/hooks");
  const Registries = require('point_of_sale.Registries');

  class BagChargesButton extends PosComponent {
       /**
            *Override PosComponent
       */
      setup() {
          useListener('click', this.onClick);
      }
    async onClick() {
    var order = this.env.pos.get_order();
    var category = this.env.pos.config.bag_category_id;
    // Select category in configuration settings
    var products = this.env.pos.db.get_product_by_category(category[0]);
    // Select products from this category
    if(products != 0) {
     // If there are products from particular category go to category screen
              this.showScreen('CategoryScreen', {
                 'bag_products': products
     });
    }
    else {
    this.showPopup('ErrorPopup', {
    // Otherwise it will a show an error popup
      'title': 'No Products Found',
      'body': 'There are no products in this category.'
    });
    }
    }
  }
BagChargesButton.template = 'BagChargesButton';
  ProductScreen.addControlButton({
  // Add button in product screen
      component: BagChargesButton,
      condition: function() {
          return this.env.pos.config.bag_charges;
      },
      position: ['before', 'SetPricelistButton'],
  });
  Registries.Component.add(BagChargesButton);
  return BagChargesButton;
});
