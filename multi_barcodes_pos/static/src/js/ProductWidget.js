/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosDB } from "@point_of_sale/app/store/db";
import { unaccent } from "@web/core/utils/strings";

patch(PosDB.prototype, {
       search_product_in_category: function(category_id, query){
            var old_query = query
            try {
            // eslint-disable-next-line no-useless-escape
            query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g, ".");
            query = query.replace(/ /g, ".+");
            var re = RegExp("([0-9]+):.*?" + unaccent(query), "gi");
            } catch {
                return [];
            }
            var results = [];
            for(var i = 0; i < this.limit; i++){
                var r = re.exec(this.category_search_string[category_id]);
                if (r) {
                    var id = Number(r[1]);
                    const product = this.get_product_by_id(id);
                    if (!this.shouldAddProduct(product, results)) {
                        continue;
                    }
                    results.push(product);
                }
                else if(this.product_by_lot_id){
                     if(this.product_by_lot_id[old_query]){
                        const product = this.get_product_by_id(this.product_by_lot_id[old_query]);
                        if (!this.shouldAddProduct(product, results)) continue;
                        if(!results.includes(product)){
                            results.push(product);
                        }
                }
                }
                else{
                    break;
                }
           }
        return results;
    }
});
