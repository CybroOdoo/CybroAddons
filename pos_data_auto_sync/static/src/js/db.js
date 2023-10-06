/** @odoo-module **/

const PosDB = require('point_of_sale.DB');
var utils = require('web.utils');
PosDB.include({
   //Overriding the add_products function for updating the products.
    add_products: function(products){
    var stored_categories = this.product_by_category_id;
    if(!(products instanceof Array)){
        products = [products];
    }
    for(var len = 0, length = products.length; len < length; len++){
        var product = products[len];
        if (product.id in this.product_by_id)continue;
        if (product.available_in_pos){
            var search_string = utils.unaccent(this._product_search_string(product));
            var categ_id = product.pos_categ_id ? product.pos_categ_id[0] : this.root_category_id;
            product.product_tmpl_id = product.product_tmpl_id[0];
            if(!stored_categories[categ_id]){
                stored_categories[categ_id] = [];
            }
            stored_categories[categ_id].push(product.id);

            if(this.category_search_string[categ_id] === undefined){
                this.category_search_string[categ_id] = '';
            }
            this.category_search_string[categ_id] += search_string;

            var ancestors = this.get_category_ancestors_ids(categ_id) || [];

            for(var j = 0, jlen = ancestors.length; j < jlen; j++){
                var ancestor = ancestors[j];
                if(! stored_categories[ancestor]){
                    stored_categories[ancestor] = [];
                }
                stored_categories[ancestor].push(product.id);

                if( this.category_search_string[ancestor] === undefined){
                    this.category_search_string[ancestor] = '';
                }
                this.category_search_string[ancestor] += search_string;
            }
        }
        this.product_by_id[product.id] = product;
        if(product.barcode){
            this.product_by_barcode[product.barcode] = product;
        }
    }
    //if the product exists, it will go to the update function.
    this.update_product(products);
    },
//    update the product values
    update_product: function(products){
        for(var len = 0, length = products.length; len < length; len++){
            var product = products[len];
            //check if the product exists or not.
            if (product.id in this.product_by_id){
            //choose the correct product for the updation.
                if(product.id == this.product_by_id[product.id].id){
                        //check the parameters one by one and update if there is any changes.
                    if (product.display_name != this.product_by_id[product.id].display_name){
                        this.product_by_id[product.id].display_name = product.display_name
                    }
                    if (product.lst_price != this.product_by_id[product.id].lst_price){
                        this.product_by_id[product.id].lst_price = product.lst_price
                    }
                    if (product.standard_price != this.product_by_id[product.id].standard_price){
                        this.product_by_id[product.id].standard_price = product.standard_price
                    }
                    if (product.categ_id != this.product_by_id[product.id].categ_id){
                        this.product_by_id[product.id].categ_id = product.categ_id
                    }
                    if (product.pos_categ_id != this.product_by_id[product.id].pos_categ_id){
                        this.product_by_id[product.id].pos_categ_id = product.pos_categ_id
                    }
                    if (product.taxes_id != this.product_by_id[product.id].taxes_id){
                        this.product_by_id[product.id].taxes_id = product.taxes_id
                    }
                    if (product.barcode != this.product_by_id[product.id].barcode){
                        this.product_by_id[product.id].barcode = product.barcode
                    }
                    if (product.default_code != this.product_by_id[product.id].default_code){
                        this.product_by_id[product.id].default_code = product.default_code
                    }
                    if (product.to_weight != this.product_by_id[product.id].to_weight){
                        this.product_by_id[product.id].to_weight = product.to_weight
                    }
                    if (product.description != this.product_by_id[product.id].description){
                        this.product_by_id[product.id].description = product.description
                    }
                    if (product.description_sale != this.product_by_id[product.id].description_sale){
                        this.product_by_id[product.id].description_sale = product.description_sale
                    }
                    if (product.l10n_in_hsn_code != this.product_by_id[product.id].l10n_in_hsn_code){
                        this.product_by_id[product.id].l10n_in_hsn_code = product.l10n_in_hsn_code
                    }
                    if (product.tracking != this.product_by_id[product.id].tracking){
                        this.product_by_id[product.id].tracking = product.tracking
                    }
                    if (product.uom_id != this.product_by_id[product.id].uom_id){
                        this.product_by_id[product.id].uom_id = product.uom_id
                    }
                }
            }
        }
    }
});
