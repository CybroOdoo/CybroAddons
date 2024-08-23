/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import {jsonrpc} from "@web/core/network/rpc_service";
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
     * 3. If "All Categories" is selected:
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
        var qry = $(ev.currentTarget).val()
        if (category === "All Categories") {
            await jsonrpc('/web/dataset/call_kw', {
                model: 'product.template',
                method: 'search_products',
                args: [qry],
                kwargs: {},
            }).then(function (result) {
                self.$('.qweb_product_id').html("");
                self.$('.qweb_product_id').append(renderToElement('website_product_search_snippet.product_template', {
                    result: result
                }));
            });
        }
        if (category === "Category") {
            var self = this;
            await jsonrpc('/web/dataset/call_kw', {
                model: 'product.template',
                method: 'product_category',
                args: [qry],
                kwargs: {},
            }).then(function (result) {
                self.$('.qweb_product_id').html("");
                self.$('.qweb_product_id').append(renderToElement('website_product_search_snippet.product_category', {
                    result: result
                }));
            });
        }
    },
    /**
     * _filterProducts: Asynchronously filters products based on the selected category.
     *
     * This function is triggered by an event (e.g., a change in category selection).
     * It checks the selected category from a dropdown menu and calls the appropriate
     * Odoo model method to fetch the relevant products. The fetched products are then
     * rendered in the specified HTML element using the corresponding QWeb template.
     *
     * @param {Object} ev - The event object associated with the action triggering this function.
     *
     * Functionality:
     * 1. Retrieves the selected category from a dropdown menu with class `.category_options`.
     * 2. If "All Categories" is selected, it calls the `search_all_categories` method
     *    on the `product.template` model to fetch all products, and renders the result
     *    using the 'website_product_search_snippet.product_template' template.
     * 3. If "Category" is selected, it calls the `product_all_categories` method on
     *    the `product.template` model to fetch products by category, and renders the
     *    result using the 'website_product_search_snippet.product_category' template.
     * 4. Updates the HTML element with class `.qweb_product_id` to display the filtered products.
     *
     * Note: The function uses `jsonrpc` to make RPC calls to the Odoo backend.
     */
    _filterProducts: async function (ev) {
        var self = this
        var category = this.$el.find(".category_options").find(":selected").text();
        if (category === "All Categories") {
            await jsonrpc('/web/dataset/call_kw', {
                model: 'product.template',
                method: 'search_all_categories',
                args: [],
                kwargs: {}
            }).then(function (result) {
                self.$('.qweb_product_id').html("");
                self.$('.qweb_product_id').append(renderToElement('website_product_search_snippet.product_template', {
                    result: result
                }));
            });
        }
        if (category === "Category") {
            await jsonrpc('/web/dataset/call_kw', {
                model: 'product.template',
                method: 'product_all_categories',
                args: [],
                kwargs: {}
            }).then(function (result) {
                self.$('.qweb_product_id').html("");
                self.$('.qweb_product_id').append(renderToElement('website_product_search_snippet.product_category', {
                    result: result
                }));
            });
        }
    },
});
publicWidget.registry.dynamic_search_snippet = Dynamic;
return Dynamic;
