odoo.define('salesperson_pos_order_line.line', function(require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    /**
     * SetProductListButton is a custom POS component that displays a list of products sorted by name.
     * Clicking the button displays a popup window that shows a list of sales persons.
     * The sales persons are passed to the popup window as a prop.
     */
    class SetProductListButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click", this.onClick);
        }
        /**
         * Gets a list of products sorted by name.
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

        // /**
        //  * Handles the click event when the button is clicked.
        //  * Displays a popup window that shows a list of sales persons.
        //  */
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
