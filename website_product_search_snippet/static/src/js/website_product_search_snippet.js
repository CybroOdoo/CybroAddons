odoo.define('website_product_search_snippet.dynamic', function(require) {
    var PublicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var Qweb = core.qweb;
    const ajax = require('web.ajax');
    var Dynamic = PublicWidget.Widget.extend({
        selector: '.dynamic_search_snippet',
        xmlDependencies: [
            "/website_product_search_snippet/static/src/xml/category_templates.xml",
            "/website_product_search_snippet/static/src/xml/product_templates.xml",
        ],
        events: {
            'click .search_container': '_onClick',
            'keyup .search_bar': '_onKeyUp',
            'change .category_options': '_filterProducts',
        },
        // When click on search bar, products/categories will displays.otherwise products/categories will not be displayed
        _onClick: function() {
            this.$el.find('#searchInput').val("");
        },
        // Call rpc query to keyup function for display all products under all category filter
        _onKeyUp: async function(ev) {
            category = this.$el.find(".category_options").find(":selected").text();
            var qry = $(ev.currentTarget).val()
            if (category === "All Categories") {
                await rpc.query({
                    model: 'product.template',
                    method: 'search_products',
                    args: [qry],
                }).then(function(result) {
                    console.log('result', this.$('.qweb_product_id'))
                    this.$('.qweb_product_id').html("");
                    this.$('.qweb_product_id').append(Qweb.render('website_product_search_snippet.product_template', {
                        'result': result
                    }));
                });
            }
            // Call rpc query to keyup function for display all category under category filter
            if (category === "Category") {
                await rpc.query({
                    model: 'product.template',
                    method: 'product_category',
                    args: [qry],
                }).then(function(result) {
                    this.$('.qweb_product_id').html("");
                    this.$('.qweb_product_id').append(Qweb.render('website_product_search_snippet.product_category', {
                        result
                    }));
                });
            }
        },
        _filterProducts: async function(ev) {
            var category = this.$el.find(".category_options").find(":selected").text();
            console.log('helloooo', category)
            var qry = $(ev.currentTarget).val()
            if (category === "All Categories") {
                await rpc.query({
                    model: 'product.template',
                    method: 'search_all_categories',
                    args: [],
                }).then(function(result) {
                    console.log('result', this)
                    this.$('.qweb_product_id').html("");
                    this.$('.qweb_product_id').append(Qweb.render('website_product_search_snippet.product_template', {
                        'result': result
                    }));
                });
            }
            if (category === "Category") {
                await rpc.query({
                    model: 'product.template',
                    method: 'product_all_categories',
                    args: [],
                }).then(function(result) {
                    this.$('.qweb_product_id').html("");
                    this.$('.qweb_product_id').append(Qweb.render('website_product_search_snippet.product_category', {
                        result
                    }));
                });
            }
        },
    });
    PublicWidget.registry.dynamic_search_snippet = Dynamic;
    return Dynamic;
});
