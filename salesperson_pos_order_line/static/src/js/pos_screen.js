/**@odoo-module **/
import PosComponent from "point_of_sale.PosComponent";
import ProductScreen from "point_of_sale.ProductScreen";
import { useListener } from "@web/core/utils/hooks";
import Registries from "point_of_sale.Registries";
import { isConnectionError } from "point_of_sale.utils";

export class SetProductListButton extends PosComponent {
    /**
     * Sets up the component and adds a click listener to the button.
     */
    setup() {
        super.setup();
        useListener("click", this.onClick);
    }
    /**
     * Returns an array of product objects fetched from the Point of Sale database and sorted by name.
     *
     * @returns {Array} The product list.
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
     * Handles the click event on the button. Opens a CustomDemoPopup allowing the user to set a salesperson for the selected product.
     *
     * @throws {Error} If an error occurs while fetching the product list or showing the CustomDemoPopup.
     */
    async onClick() {
        try {
            let list = this.productsList;
            this.showPopup("SalesPersonPopup", {
                'user_id': this.env.pos.res_users
            });

        } catch (error) {
            if (isConnectionError(error)) {
                this.showPopup("ErrorPopup", {
                    title: this.env._t("Network Error"),
                    body: this.env._t("Cannot access Product screen if offline."),
                });
            } else {
                throw error;
            }
        }
    }
}
SetProductListButton.template = "SalesPersonButton";
ProductScreen.addControlButton({
    component: SetProductListButton,
    condition: function() {
        return true;
    },
});
Registries.Component.add(SetProductListButton);
