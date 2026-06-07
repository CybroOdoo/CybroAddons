/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import {renderToElement} from "@web/core/utils/render";

var Dynamic = publicWidget.Widget.extend({
    selector: '.dynamic_search_snippet',
    events: {
        'click .search_container': '_onClick',
        'keyup .search_bar': '_onKeyUp',
        'change .category_options': '_filterProducts',
    },
    /**
     * _onClick: Clears the search input field.
     *
     * This function is triggered when a specific element is clicked. It clears the value of
     * the input field with the ID `#searchInput`.
     *
     * Functionality:
     * 1. Locates the input field with the ID `#searchInput` within the current element (`this.$el`).
     * 2. Sets the value of the `#searchInput` field to an empty string, effectively clearing any text that was entered.
     */
    _onClick: function () {
        this.$el.find('#searchInput').val("");
    },
    /**
     * Clear the rendered search results.
     */
    _clearResults: function () {
        this.$('.qweb_product_id').html("");
    },
    /**
     * _onKeyUp: Asynchronously searches and filters products based on the user's input and selected category.
     *
     * This function is triggered when a key is released while typing in a search input field.
     * It captures the current search query and the selected category, then calls the appropriate
     * Odoo model method to fetch the relevant products. The fetched products are rendered in the
     * specified HTML element using the corresponding QWeb template.
     *
     * @param {Object} ev - The event object associated with the keyup action.
     *
     * Functionality:
     * 1. Captures the selected category from a dropdown menu with the class `.category_options`.
     * 2. Retrieves the user's search query from the input field.
     * 3. If "Products" is selected:
     *    - Calls the `search_products` method on the `product.template` model with the search query as an argument.
     *    - Renders the result using the 'website_product_search_snippet.product_template' template.
     * 4. If "Category" is selected:
     *    - Calls the `product_category` method on the `product.template` model with the search query as an argument.
     *    - Renders the result using the 'website_product_search_snippet.product_category' template.
     * 5. Updates the HTML element with the class `.qweb_product_id` to display the filtered products based on the search query and selected category.
     *
     * Note: The function uses `jsonrpc` to make RPC calls to the Odoo backend.
     */
    _onKeyUp: async function (ev) {
        var self = this;
        var category = this.$el.find(".category_options").find(":selected").text();
        var qry = $(ev.currentTarget).val().trim();
        if (!qry) {
            this._clearResults();
            return;
        }
        if (category === "Products") {
            await rpc('/web/dataset/call_kw', {
                model: 'product.template',
                method: 'search_products',
                args: [qry],
                kwargs: {},
            }).then(function (result) {
                self._clearResults();
                self.$('.qweb_product_id').append(renderToElement('website_product_search_snippet.product_template', {
                    result: result
                }));
            });
        }
        if (category === "Category") {
            var self = this;
            await rpc('/web/dataset/call_kw', {
                model: 'product.template',
                method: 'product_category',
                args: [qry],
                kwargs: {},
            }).then(function (result) {
                self._clearResults();
                self.$('.qweb_product_id').append(renderToElement('website_product_search_snippet.product_category', {
                    result: result
                }));
            });
        }
    },
    /**
     * Reset the search state when the dropdown option changes.
     *
     * This prevents stale results from the previous selection from remaining
     * visible under the newly selected mode.
     */
    _filterProducts: function () {
        this.$el.find('#searchInput').val("");
        this._clearResults();
    },
});
publicWidget.registry.dynamic_search_snippet = Dynamic;
return Dynamic;
