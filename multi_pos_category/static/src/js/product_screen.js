odoo.define('multi_pos_category.product_product', function (require) {
    'use strict';
    const DB = require('point_of_sale.DB');
    var utils = require('web.utils');
    DB.include({
        init: function (options) {
            this._super.apply(this, arguments);
        },
        get_product_by_category: function (category_id) {
            /* This function will be used to Retrieves the product by user selecting category wise*/
            var list = [];

            if (category_id != 0) {
                // For specific category - get all products and filter
                var all_products = this.product_by_id;

                for(var product_id in all_products) {
                    var product = all_products[product_id];

                    // Skip inactive products
                    if (!(product.active && product.available_in_pos)) continue;

                    // Check if product belongs to the selected category
                    var belongs_to_category = false;

                    // Check pos_categ_ids (multi-category field)
                    if (product.pos_categ_ids && product.pos_categ_ids.length > 0) {
                        if (product.pos_categ_ids.indexOf(category_id) !== -1) {
                            belongs_to_category = true;
                        }
                    }

                    // Also check pos_categ_id (single category field for compatibility)
                    if (!belongs_to_category && product.pos_categ_id == category_id) {
                        belongs_to_category = true;
                    }

                    if (belongs_to_category) {
                        list.push(product);
                    }
                }

                // Apply limit
                if (this.limit && list.length > this.limit) {
                    list = list.slice(0, this.limit);
                }
            } else {
                // For "All" category - use original logic
                var product_ids = this.product_by_category_id["undefined"];
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
            /* Searches for products within a specific category based on the provided query.*/
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
            } catch(_e) {
                return [];
            }
            var results = [];
            for(var i = 0; i < this.limit; i++) {
                var r = re.exec(this.category_search_string[categ]);
                if(r) {
                    var id = Number(r[1]);
                    const product = this.get_product_by_id(id);
                    if (!(product.active && product.available_in_pos)) continue;

                    // Check if product belongs to the selected category (if not searching in "All")
                    if (category_id != 0) {
                        var belongs_to_category = false;

                        // Check pos_categ_ids (multi-category field)
                        if (product.pos_categ_ids && product.pos_categ_ids.length > 0) {
                            if (product.pos_categ_ids.indexOf(category_id) !== -1) {
                                belongs_to_category = true;
                            }
                        }

                        // Also check pos_categ_id (single category field for compatibility)
                        if (!belongs_to_category && product.pos_categ_id == category_id) {
                            belongs_to_category = true;
                        }

                        if (!belongs_to_category) {
                            continue;
                        }
                    }
                    results.push(product);
                } else {
                    break;
                }
            }
            return results;
        },
    });
    return DB;
});