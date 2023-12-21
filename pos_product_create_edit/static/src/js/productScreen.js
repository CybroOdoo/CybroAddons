/**@odoo-module **/

import ControlButtonsMixin from "point_of_sale.ControlButtonsMixin";
import Registries from "point_of_sale.Registries";
import IndependentToOrderScreen from "point_of_sale.IndependentToOrderScreen";
import { useListener } from "@web/core/utils/hooks";
import PosComponent from "point_of_sale.PosComponent";
import { Gui } from "point_of_sale.Gui";
const { useRef } = owl.hooks;

class ProductListScreen extends PosComponent {
  setup() {
    super.setup();
    this.searchWordInputRef = useRef("search-word-input-product");
    this.state = {
      search: null,
    };
  }
  /**
   * Create a new product by showing the CreateProductPopup.
   */
  createProduct() {
    this.showPopup("CreateProductPopup", {
      product: this.props.product,
    });
  }
  /**
   * Get the list of products to display.
   * @returns {Array} The list of products.
   */
  get products() {
    let list;
    if (this.state.search && this.state.search.trim() !== "") {
      list = this.env.pos.db.search_product_in_category(
        0,
        this.state.search.trim()
      );
    } else {
      list = this.env.pos.db.get_product_by_category(0);
    }
    return list.sort(function (a, b) {
      return a.display_name.localeCompare(b.display_name);
    });
  }
  /**
   * Update the product list based on the search input.
   * @param {Event} event - The event object.
   */
  async updateProductList(event) {
    this.state.search = event.target.value;
    if (event.code === "Enter") {
      this._onPressEnterKey();
    } else {
      this.render(true);
    }
  }
  /**
   * Handle the Enter key press event.
   */
  async _onPressEnterKey() {
    if (!this.state.search) return;
    if (!this.env.pos.isEveryProductLoaded) {
      const result = await this.products;
      this.showNotification(
        _.str.sprintf(
          this.env._t('%s Product(s) found for "%s".'),
          result.length,
          this.state.search
        ),
        3000
      );
      if (!result.length) this._clearSearch();
    }
  }
  /**
   * Clear the search input and reset the search state.
   */
  _clearSearch() {
    this.searchWordInputRef.el.value = "";
    this.state.search = "";
    this.render(true);
  }
  /**
   * Navigate back to the ProductScreen.
   */
  back() {
    this.showScreen('ProductScreen');
    }
}
ProductListScreen.template = "ProductListScreen";
Registries.Component.add(ProductListScreen);
