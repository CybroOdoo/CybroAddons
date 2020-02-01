odoo.define('discount_limit.editor', function (require) {
    'use strict';


var models = require('point_of_sale.models');
var pos_disc = require('point_of_sale.screens');
var core = require('web.core');
var _t = core._t;
models.load_fields('pos.category', 'discount_limit');
models.load_fields('product.product', 'product_discount_limit');

pos_disc.OrderWidget.include({

    set_value: function(val) {
        console.log("ddddd")
    	var order = this.pos.get_order();
    	var prod_id = order.selected_orderline.product.pos_categ_id[0]
    	 if(this.pos.config.apply_discount_limit == 'product_category'){
    	if (order.get_selected_orderline()) {
            var mode = this.numpad_state.get('mode');
            if( mode === 'quantity'){
                order.get_selected_orderline().set_quantity(val);
            }else if( mode === 'discount'){
            var mi = Math.round(val)
            if(Number.isInteger(prod_id)){

                if(this.pos.db.category_by_id[prod_id].discount_limit){
                    if (mi > this.pos.db.category_by_id[prod_id].discount_limit){
                        this.gui.show_popup('error', {
                            title : _t("Discount Not Possible"),
                            body  : _t("You cannot apply discount above the discount limit."),
                        });
                        order.get_selected_orderline().set_discount(0);
                            this.numpad_state.reset();
                        return;
                    }
                    else
                    {
                        order.get_selected_orderline().set_discount(val);
                    }
                 }

                 else{
                         order.get_selected_orderline().set_discount(val);
                    }
              }
                 else{
                         order.get_selected_orderline().set_discount(val);
                 }

            }else if( mode === 'price'){
                var selected_orderline = order.get_selected_orderline();
                selected_orderline.price_manually_set = true;
                selected_orderline.set_unit_price(val);
            }
    	}
    	}
    	else if(this.pos.config.apply_discount_limit == 'product'){
    	var product_id = order.selected_orderline.product

    	if (order.get_selected_orderline()) {
            var mode = this.numpad_state.get('mode');
            if( mode === 'quantity'){
                order.get_selected_orderline().set_quantity(val);
            }


            else if( mode === 'discount'){
            var mi = Math.round(val)

                if (product_id.product_discount_limit>0){
                    if (mi > product_id.product_discount_limit){
                        this.gui.show_popup('error', {
                            title : _t("Discount Not Possible"),
                            body  : _t("You cannot apply discount above the discount limit."),
                        });
                        order.get_selected_orderline().set_discount(0);
                            this.numpad_state.reset();
                        return;
                    }
                    else
                    {
                        order.get_selected_orderline().set_discount(val);
                    }
                    }
                    else
                    {
                        order.get_selected_orderline().set_discount(val);
                    }
            }

            else if( mode === 'price'){
                var selected_orderline = order.get_selected_orderline();
                selected_orderline.price_manually_set = true;
                selected_orderline.set_unit_price(val);
            }
    	}
    	    
    	}
    },

    });

});



