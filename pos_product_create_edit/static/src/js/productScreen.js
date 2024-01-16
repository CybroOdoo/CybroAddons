odoo.define("pos_product_create_edit.productScreen", function (require) {
    "use strict";
    const Registries = require("point_of_sale.Registries");
    const PosComponent = require("point_of_sale.PosComponent");
    const { useRef } = owl.hooks;
    class ProductListScreen extends PosComponent {
    constructor() {
        super(...arguments);
        this.searchWordInputRef = useRef("search-word-input-product");
        this.state = {
            search: null,
        };
    }
    /**
     * Open the CreateProductPopup to create a new product.
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
        return list.sort(function(a, b) {
            return a.display_name.localeCompare(b.display_name);
        });
    }
    /**
     * Update the product list based on the search input.
     * @param {Event} event - The input event.
     */
    async updateProductList(event) {
        this.state.search = event.target.value;
        if (event.code === "Enter") {
            await this._onPressEnterKey();
        } else {
            this.render(true);
        }
    }
    /**
     * Handle the press of the Enter key in the search input.
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
     * Go back to the ProductScreen.
     */
    back() {
        this.showScreen("ProductScreen");
    }
    }
    ProductListScreen.template = "ProductListScreen";
    Registries.Component.add(ProductListScreen);
    return ProductListScreen;
});
