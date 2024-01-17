/**@odoo-module **/
import PosComponent from "point_of_sale.PosComponent";
import ProductScreen from "point_of_sale.ProductScreen";
import { useListener } from "@web/core/utils/hooks";
import Registries from "point_of_sale.Registries";
import { Gui } from "point_of_sale.Gui";
import { isConnectionError } from "point_of_sale.utils";
//A custom component that adds a control button to set the product list based on the selected category.
export class SetProductListButton extends PosComponent {
  setup() {//Sets up the component by initializing the event listener.
    super.setup();
    useListener("click", this.onClick);
  }
  get productsList() {//Retrieves the product list based on the selected category. @returns {Array} The sorted product list.
    let list = [];
    list = this.env.pos.db.get_product_by_category(
      this.env.pos.selectedCategoryId
    );
    return list.sort(function (a, b) {
      return a.display_name.localeCompare(b.display_name);
    });
  }
  async onClick() {//Handles the click event when the button is clicked.
    try {
      let list = this.productsList;
      const screen = "ProductListScreen";
      Gui.showScreen(screen);
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
    condition: function () {
        return true;
    },
});
Registries.Component.add(SetProductListButton);
