odoo.define('all_in_one_pos_kit.product', function(require) {
    "use strict";
    var rpc = require('web.rpc');
    var DB = require('point_of_sale.DB');
    var utils = require('web.utils');
    const Registries = require('point_of_sale.Registries');
    DB.include({ // Extends the DB object to add multi barcode to product.
        init: function(options) { //Initializes the object.
            this._super.apply(this, arguments);
        },
        add_products: function(products) { //Function to add multi barcode product in pos session.
            var stored_categories = this.product_by_category_id;
            if (!products instanceof Array) {
                products = [products];
            }
            for (var i = 0, len = products.length; i < len; i++) {
                var product = products[i];
                if (product.id in this.product_by_id) continue;
                if (product.available_in_pos) {
                    var search_string = utils.unaccent(this._product_search_string(product));
                    var categ_id = product.pos_categ_id ? product.pos_categ_id[0] : this.root_category_id;
                    product.product_tmpl_id = product.product_tmpl_id[0];
                    if (!stored_categories[categ_id]) {
                        stored_categories[categ_id] = [];
                    }
                    stored_categories[categ_id].push(product.id);
                    if (this.category_search_string[categ_id] === undefined) {
                        this.category_search_string[categ_id] = '';
                    }
                    this.category_search_string[categ_id] += search_string;
                    var ancestors = this.get_category_ancestors_ids(categ_id) || [];
                    for (var j = 0, jlen = ancestors.length; j < jlen; j++) {
                        var ancestor = ancestors[j];
                        if (!stored_categories[ancestor]) {
                            stored_categories[ancestor] = [];
                        }
                        stored_categories[ancestor].push(product.id);
                        if (this.category_search_string[ancestor] === undefined) {
                            this.category_search_string[ancestor] = '';
                        }
                        this.category_search_string[ancestor] += search_string;
                    }
                }
                this.product_by_id[product.id] = product;
                if (product.barcode) {
                    this.product_by_barcode[product.barcode] = product;
                }
                for (var t = 0; t < product.product_multi_barcodes_ids.length; t++) {
                    var self = this;
                    rpc.query({
                        model: 'multi.barcode.product',
                        method: 'get_barcode_val',
                        args: [product.product_multi_barcodes_ids[t], product.id],
                    }).then(function(barcode_val) {
                        self.product_by_barcode[barcode_val[0]] = self.product_by_id[barcode_val[1]];
                    });
                }
            }
        },
    });
});
