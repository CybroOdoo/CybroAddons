odoo.define('multi_pos_category.product_product', function (require) {
    'use strict';
    const DB = require('point_of_sale.DB');
    var utils = require('web.utils');
    DB.include({
        init: function (options) {
            this._super.apply(this, arguments);
            this.get_product_by_category();
            this.search_product_in_category();
        },
        get_product_by_category: function (category_id) {
        /* This function will be used to Retrieves the product by user selecting category wise*/
            var list = [];
            if (category_id!=0){
                var products = this.product_by_category_id[0];
                 // Iterate through each product
                for(const key in products){
                    var list_product = [];
                                // Retrieve the list of pos_categ_id values for the current product
                    for(const keys in this.product_by_id[products[key]].pos_categ_id){
                        list_product.push(this.product_by_id[products[key]].pos_categ_id[keys])
                    }
                                // Check if the category_id is present in the list of pos_categ_id values
                    if(jQuery.inArray(category_id, list_product) !== -1){
                        list.push(this.product_by_id[products[key]]);
                    }
                }
            }
            else{
                    // Retrieve the product_ids associated with the "0" category
                var product_ids  = this.product_by_category_id["undefined"];
                if (product_ids) {
                    for (var i = 0, len = Math.min(product_ids.length, this.limit); i < len; i++) {
                        const product = this.product_by_id[product_ids[i]];
                        if (!(product.active && product.available_in_pos)) continue;
                        list.push(product);
                    }
                }
            }
        return list;
        },
        search_product_in_category: function (category_id, query) {
/*       Searches for products within a specific category based on the provided query.*/
            if (category_id == 0) {
                var categ = "undefined";
            } else {
                var categ = category_id;
            }
             try {
                        // Prepare the search query by replacing special characters and spaces
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(/ /g,'.+');
                        // Create a regular expression with the search query and unaccented characters
                var re = RegExp("([0-9]+):.*?"+utils.unaccent(query),"gi");
            }catch(_e){
                return [];
            }
            var results = [];
            for(var i = 0; i < this.limit; i++){
                var r = re.exec(this.category_search_string[categ]);
                if(r){
                    var id = Number(r[1]);
                    const product = this.get_product_by_id(id);
                    if (!(product.active && product.available_in_pos)) continue;
                    results.push(product);
                }else{
                    break;
                }
            }
            return results;
        },
    });
    return DB;
});
