/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosDB } from "@point_of_sale/app/store/db";
import { unaccent } from "@web/core/utils/strings";
import { jsonrpc } from "@web/core/network/rpc_service";

patch(PosDB.prototype, {
      add_products(products) {
      //Extends the add_products method of the PosDB class to include additional functionality for handling product barcodes.
        var stored_categories = this.product_by_category_id;
        if (!(products instanceof Array)) {
            products = [products];
        }
        for (var i = 0, len = products.length; i < len; i++) {
            var product = products[i];
            if (product.id in this.product_by_id) {
                continue;
            }
            if (product.available_in_pos) {
                var search_string = unaccent(this._product_search_string(product));
                const all_categ_ids = product.pos_categ_ids.length
                    ? product.pos_categ_ids
                    : [this.root_category_id];
                product.product_tmpl_id = product.product_tmpl_id[0];
                for (const categ_id of all_categ_ids) {
                    if (!stored_categories[categ_id]) {
                        stored_categories[categ_id] = [];
                    }
                    stored_categories[categ_id].push(product.id);
                    if (this.category_search_string[categ_id] === undefined) {
                        this.category_search_string[categ_id] = "";
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
                            this.category_search_string[ancestor] = "";
                        }
                        this.category_search_string[ancestor] += search_string;
                    }
                }
            }
            this.product_by_id[product.id] = product;
            if (product.barcode && product.active) {
                this.product_by_barcode[product.barcode] = product;
            }
            for (var t = 0; t < product.product_multi_barcodes_ids.length; t++) {
                    var self = this;
                         jsonrpc('/web/dataset/call_kw/multi.barcode.products/get_barcode_val', {
                                    model: 'multi.barcode.products',
                                    method: 'get_barcode_val',
                                    args: [product.product_multi_barcodes_ids[t], product.id],
                                    kwargs: {},
                                }).then(function(barcode_val) {
                                      self.product_by_barcode[barcode_val[0]] = self.product_by_id[barcode_val[1]];
                         });
            }
        }
         return super.add_products(products);
    },
});