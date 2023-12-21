/**@odoo-module **/

import PosComponent from "point_of_sale.PosComponent";
import ProductScreen from "point_of_sale.ProductScreen";
import { useListener } from "@web/core/utils/hooks";
import Registries from "point_of_sale.Registries";
import { Gui } from "point_of_sale.Gui";
import { isConnectionError } from "point_of_sale.utils";
export class SetProductListButton extends PosComponent {
    /**
     * Set up the component and attach the click event listener.
     */
    setup() {
        super.setup();
        useListener("click", this.onClick);
    }
   /**
   * Get the list of products filtered by the selected category.
   * @returns {Array} The sorted list of products.
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
   * Handle the click event of the button.
   */
    async onClick() {
        try {
            let list = this.productsList;
            const screen = "ProductListScreen";
            this.showScreen(screen);
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
SetProductListButton.template = "SetProductListButton";
ProductScreen.addControlButton({
    component: SetProductListButton,
    condition: function() {
        return true;
    },
});
Registries.Component.add(SetProductListButton);
