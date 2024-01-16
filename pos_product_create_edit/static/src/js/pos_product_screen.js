odoo.define("pos_product_create_edit.pos_product_screen", function(require) {
    "use strict";
    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require('web.custom_hooks');
    const Registries = require("point_of_sale.Registries");
    const { isRpcError } = require('point_of_sale.utils');
    class SetProductListButton extends PosComponent {
        /**
         * Sets up the component.
         * Attaches a click listener to the button.
         */
        setup() {
            super.setup();
            useListener("click", this.onClick);
        }
        /**
         * Retrieves the product list based on the selected category ID.
         * @returns {Array} The sorted product list.
         */
        get productsList() {
            let list = [];
            list = this.env.pos.db.get_product_by_category(
                this.env.pos.selectedCategoryId
            );
            return list.sort(function(a, b) {
                return a.display_name.localeCompare(b.display_name);
            });
        }
        /**
         * Handles the click event of the button.
         * Shows the product list screen.
         */
        async onClick() {
            try {
                let list = this.productsList;
                const screen = "ProductListScreen";
                this.showScreen(screen);
            } catch (error) {
                if (isRpcError(error) && error.message.code < 0) {
                    Gui.showPopup('ErrorPopup', {
                        title: this.comp.env._t('Network Error'),
                        body: this.comp.env._t('Cannot access Product screen if offline.'),
                    });
                    Gui.setSyncStatus('error');
                } else {
                    throw error;
                }
            }
        }
    }
    /**
     * Adds the custom button to the ProductScreen control buttons.
     */
    SetProductListButton.template = "SetProductListButton";
    ProductScreen.addControlButton({
        component: SetProductListButton,
        condition: function() {
            return true;
        },
    });
    Registries.Component.add(SetProductListButton);
    return SetProductListButton;
});
