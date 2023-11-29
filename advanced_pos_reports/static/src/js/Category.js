odoo.define('advanced_pos_reports.CategorySummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");
    class CategorySummaryButton extends PosComponent {
         /**
            * @Override PosComponent
         */
         setup() {
             useListener('click', this._onClick);
        }
        _onClick() {
            //Show category summary popup
            this.showPopup('CategorySummaryPopup',
                            { title: 'Category Summary',}
                          );
        }
    }
    CategorySummaryButton.template = 'CategorySummaryButton';
    ProductScreen.addControlButton({
      // Add button in product screen
        component: CategorySummaryButton,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(CategorySummaryButton);
    return CategorySummaryButton;
});
