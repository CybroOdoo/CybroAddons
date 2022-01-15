odoo.define('discount_limit.DiscountLimit', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var field_utils = require('web.field_utils');
    var core = require('web.core');
    const _t = core._t;
    const { Gui } = require('point_of_sale.Gui');
    models.load_fields('pos.category', 'discount_limit');
    models.load_fields('product.product', 'product_discount_limit');
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        set_discount: function(discount){
            var order = this.pos.get_order();
            var pos_prod_id = order.selected_orderline.product.pos_categ_id[0]
            if(this.pos.config.apply_discount_limit == false){

                var parsed_discount = isNaN(parseFloat(discount)) ? 0 : field_utils.parse.float('' + discount);
                var disc = Math.min(Math.max(parsed_discount || 0, 0),100);
                this.discount = disc;
                this.discountStr = '' + disc;
                this.trigger('change',this);
            } else if(this.pos.config.apply_discount_limit == 'product_category'){
               var rounded = Math.round(discount);
                if(Number.isInteger(pos_prod_id)){
                    if(this.pos.db.category_by_id[pos_prod_id].discount_limit){

                        if(rounded > this.pos.db.category_by_id[pos_prod_id].discount_limit){
                            Gui.showPopup("ErrorPopup", {
                                'title': _t("Discount Not Possible"),
                                'body':  _t("You cannot apply discount above the discount limit."),
                            });
                        } else {
                            var parsed_discount = isNaN(parseFloat(rounded)) ? 0 : field_utils.parse.float('' + rounded);
                            var disc = Math.min(Math.max(parsed_discount || 0, 0),100);
                            this.discount = disc;
                            this.discountStr = '' + disc;
                            this.trigger('change',this);
                        }
                    } else {
                        var parsed_discount = isNaN(parseFloat(rounded)) ? 0 : field_utils.parse.float('' + rounded);
                        var disc = Math.min(Math.max(parsed_discount || 0, 0),100);
                        this.discount = disc;
                        this.discountStr = '' + disc;
                        this.trigger('change',this);
                    }
                }
            }else if(this.pos.config.apply_discount_limit == 'product'){
                var rounded = Math.round(discount);
                if(Number.isInteger(pos_prod_id)){
                     if(this.get_product().product_discount_limit){
                        if(rounded > this.get_product().product_discount_limit){
                            Gui.showPopup("ErrorPopup", {
                                'title': _t("Discount Not Possible"),
                                'body':  _t("You cannot apply discount above the discount limit."),
                            });
                        } else {
                            var parsed_discount = isNaN(parseFloat(rounded)) ? 0 : field_utils.parse.float('' + rounded);
                            var disc = Math.min(Math.max(parsed_discount || 0, 0),100);
                            this.discount = disc;
                            this.discountStr = '' + disc;
                            this.trigger('change',this);
                        }
                    } else {
                        var parsed_discount = isNaN(parseFloat(rounded)) ? 0 : field_utils.parse.float('' + rounded);
                        var disc = Math.min(Math.max(parsed_discount || 0, 0),100);
                        this.discount = disc;
                        this.discountStr = '' + disc;
                        this.trigger('change',this);
                    }
                }
            }


        },
    });
});

