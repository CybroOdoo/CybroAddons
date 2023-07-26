odoo.define('pos_product_search_by_ref.product_product', function (require) {
    'use strict';
    const DB = require('point_of_sale.DB');
    var core = require('web.core');
    var utils = require('web.utils');
     DB.include({
        search_product_in_category: function(category_id, query){
            var old_query = query
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(/ /g,'.+');
                var re = RegExp("([0-9]+):.*?"+utils.unaccent(query),"gi");
            }catch(_e){
                return [];
            }
            var results = [];
            for(var i = 0; i < this.limit; i++){
                var r = re.exec(this.category_search_string[category_id]);
                if(r){
                    var id = Number(r[1]);
                    const product = this.get_product_by_id(id);
                    if (!(product.active && product.available_in_pos)) continue;
                    results.push(product);
                }else if(this.product_by_lot_id[old_query]){
                        const product = this.get_product_by_id(this.product_by_lot_id[old_query]);
                        if (!(product.active && product.available_in_pos)) continue;
                        if(!results.includes(product)){
                            results.push(product);
                        }
                }else{
                    break;
                }
            }
        return results;
        }
     })
    return DB;
});