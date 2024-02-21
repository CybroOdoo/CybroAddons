/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { registry } from '@web/core/registry';
import { renderToElement } from "@web/core/utils/render";
import { onWillStart } from "@odoo/owl";
     /**
     * Widget for displaying top-selling products in categories.
     */
publicWidget.registry.TopSellingProducts = publicWidget.Widget.extend({
        selector: '.products_category_wise_snippet',
        /**
         * Load products and categories data from the server.
         */
   init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },
        /**
         * Render the widget with the fetched data.
         */
        start: async function() {
            await this.rpc('/top_products/categories', {}).then((data) => {
                this.products = data[0];
                this.categories = data[1];
                this.website_id = data[2];
            })
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
                renderToElement('top_selling_product_in_category.products_category_wise', {
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
