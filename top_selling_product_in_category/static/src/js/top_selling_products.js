odoo.define('top_selling_product_in_category.top_selling_products', function(require) {
    "use strict";
    var PublicWidget = require('web.public.widget')
    var ajax = require('web.ajax');
    var core = require('web.core')
    var Qweb = core.qweb;
     /**
     * Widget for displaying top-selling products in categories.
     */
    var TopSellingProducts = PublicWidget.Widget.extend({
        selector: '.products_category_wise_snippet',
        /**
         * Load products and categories data from the server.
         */
        willStart: async function() {
            await ajax.jsonRpc('/top_products/categories', 'call', {}).then((data) => {
                this.products = data[0];
                this.categories = data[1];
                this.website_id = data[2];
            })
        },
        /**
         * Render the widget with the fetched data.
         */
        start: function() {
            var products = this.products
            var categories = this.categories
            const current_website_id = this.website_id
            var products_list=[]
            categories.forEach(function(category){
                var product_category=products.filter(function(product){
                    return product.public_categ_ids[0] === category.id;
                })
                var chunks=[];
                for (var i=0;i<product_category.length;i+=4){
                    chunks.push(product_category.slice(i,i+4))
                }
                if (chunks.length>1){
                    chunks[0].is_active=true
                    chunks.push('chunk')
                }
                products_list.push({
                    'category':category,
                    'products':chunks
                })
            })
            this.$el.find('#top_products_carousel').html(
                Qweb.render('top_selling_product_in_category.products_category_wise', {
                    products,
                    categories,
                    current_website_id,
                    products_list
                })
            )
            const emptyDiv = document.querySelectorAll('.top_selling')
            emptyDiv.forEach(div =>{
            if(div.firstElementChild == null){
                div.remove()
            }
            })
            const carouselItem = document.querySelectorAll('.top')
            carouselItem.forEach(item=>{
                if(item.firstElementChild == null){
                item.remove()
            }
            })
        },
    })
    PublicWidget.registry.products_category_wise_snippet = TopSellingProducts;
    return TopSellingProducts;
})
