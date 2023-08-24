odoo.define('salesperson_pos_order_line.line', function(require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    class SetProductListButton extends PosComponent {
        /**
         * This class represents a button in the POS product screen that, when clicked,
         * displays a custom popup with a list of salespersons to choose from.
         */
        constructor() {
            super(...arguments);
            useListener("click", this.onClick);
        }
        /**
         * Returns an array of product objects filtered by the currently selected category.
         *
         * @returns {Array} An array of product objects.
         */
        get productsList() {
            let list = [];
            list = this.env.pos.db.get_product_by_category(
                this.env.pos.selectedCategoryId
            );
            return list.sort(function (a, b) {
                return a.display_name.localeCompare(b.display_name);
            });
        }
        /**
         * Handles the click event on the custom product button and displays the custom popup.
         */
        async onClick() {
            let list = this.productsList;
            this.showPopup("CustomDemoPopup",{'sales_persons':this.env.pos.users});
        }
    }
    SetProductListButton.template = "CustomDemoButtons";
    ProductScreen.addControlButton({
        component: SetProductListButton,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(SetProductListButton);
});
