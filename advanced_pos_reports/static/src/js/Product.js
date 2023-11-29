odoo.define('advanced_pos_reports.ProductSummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");

    class ProductSummaryButton extends PosComponent {
       /**
            * @Override PosComponent
       */
      setup() {
            useListener('click', this._onClick);
      }
        _onClick() {
            //Show product summary popup
            this.showPopup('ProductSummaryPopup', { title: 'Product Summary', });
        }
    }
    ProductSummaryButton.template = 'ProductSummaryButton';
    ProductScreen.addControlButton({
      // Add button in product screen
        component: ProductSummaryButton,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(ProductSummaryButton);
    return ProductSummaryButton;
});
