/**@odoo-module **/
import Registries from "point_of_sale.Registries";
import PosComponent from "point_of_sale.PosComponent";
import { useRef } from "@odoo/owl";
//A custom component representing the screen for displaying a list of products.
class ProductListScreen extends PosComponent {
  setup() {//Sets up the component.
    super.setup();
    this.searchWordInputRef = useRef("search-word-input-product");
    this.state = {
      search: null,
    };
  }
  createProduct() {//Opens the create product popup.
    this.showPopup("CreateProductPopup", {
      product: this.props.product,
    });
  }
  get products() {//Retrieves the list of products based on the search input and category. @returns {Array} The list of products.
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
  async updateProductList(event) {//Updates the product list based on the search input.
    this.state.search = event.target.value;
    if (event.code === "Enter") {
      this._onPressEnterKey();
    } else {
      this.render(true);
    }
  }
  async _onPressEnterKey() {//Handles the "Enter" key press event.
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
  _clearSearch() {//Clears the search input and resets the state
    this.searchWordInputRef.el.value = "";
    this.state.search = "";
    this.render(true);
  }
  back() {//Navigates back to the product screen.
    this.showScreen('ProductScreen');
    }
}
ProductListScreen.template = "ProductListScreen";
Registries.Component.add(ProductListScreen);
