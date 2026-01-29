odoo.define('top_selling_product_in_category.products_category_wise', function (require) {
'use strict';
var core = require('web.core');
var publicWidget = require('web.public.widget');
var rpc = require('web.rpc');
const ajax = require('web.ajax');
var qweb = core.qweb;

publicWidget.registry.TopSellingProducts = publicWidget.Widget.extend({
    xmlDependencies: ['/top_selling_product_in_category/static/src/xml/top_selling_products_templates.xml'],
    selector: '.products_category_wise_snippet',
    /**
     * Load products and categories data from the server.
     */
    willStart: async function () {
        await rpc.query({ route: '/top_products/categories' }).then((data) => {
            this.products = data[0];
            this.categories = data[1];
            this.website_id = data[2];
        });
        var proms = [];
        if (this.xmlDependencies) {
            proms.push.apply(proms, _.map(this.xmlDependencies, function (xmlPath) {
                return ajax.loadXML(xmlPath, core.qweb);
            }));
        }
        return Promise.all(proms);
    },
    /**
     * Render the widget with the fetched data.
     */
    start: function () {
        var products = this.products;
        var categories = this.categories;
        const current_website_id = this.website_id;
        var products_list = [];
        categories.forEach(function (category) {
            var product_category = products.filter(function (product) {
                return product.public_categ_ids[0] === category.id;
            });
            var chunks = [];
            for (var i = 0; i < product_category.length; i += 4) {
                chunks.push(product_category.slice(i, i + 4));
            }
            if (chunks.length > 1) {
                chunks[0].is_active = true;
                chunks.push('chunk');
            }
            products_list.push({
                'category': category,
                'products': chunks
            });
        });
        this.$el.find('#top_products_carousel').html(
            qweb.render('top_selling_product_in_category.products_category_wise', {
                products: products,
                categories: categories,
                current_website_id: current_website_id,
                products_list: products_list
            })
        );
        const emptyDiv = document.querySelectorAll('.top_selling');
        emptyDiv.forEach(div => {
            if (div.firstElementChild == null) {
                div.remove();
            }
        });
        const carouselItem = document.querySelectorAll('.top');
        carouselItem.forEach(item => {
            if (item.firstElementChild == null) {
                item.remove();
            }
        });
    },
});
return publicWidget.registry.TopSellingProducts;
});