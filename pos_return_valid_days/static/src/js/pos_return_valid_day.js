odoo.define('pos_return_valid_days.valid', function (require) {
"use strict";

    var pos_model = require('point_of_sale.models');
    var models = pos_model.PosModel.prototype.models;
    var orderline_id =1;
    for(var i=0; i<models.length; i++){
        var model=models[i];
        if(model.model === 'pos.category'){
             model.fields.push('valid_day');
        }
    }
    var category=[];
    pos_model.Orderline = pos_model.Orderline.extend({
        initialize: function(attr,options){
        this.pos   = options.pos;
        this.order = options.order;
        if (options.json) {
            this.init_from_JSON(options.json);
            return;
        }
        this.product = options.product;
        this.price   = options.product.price;
        this.set_quantity(1);
        this.discount = 0;
        this.discountStr = '0';
        this.type = 'unit';
        this.selected = false;
        this.count = true;
        this.category_selected = true;
        this.select = false;
        this.id       = orderline_id++;
   },
    get_category_validity : function(){
        var self = this;
        category=this.product.pos_categ_id[0];
        var validity = this.pos.db.get_category_by_id(category);
        return (validity ? validity.valid_day : undefined) || '';
    },
    get_category : function(){
        var product = this.product.pos_categ_id[1];
        return (product ? this.product.pos_categ_id[1] : undefined) || '';
   },
   get_category_id: function(){
            return this.product.pos_categ_id[0];
   },
   set_selected_product: function(count){
            this.count = count;
            this.trigger('change',this);
   },
   set_selected_category: function(selected){
        this.category_selected = selected;
        this.trigger('change',this);
   },
   is_selected_product: function(){
        return this.count;
   },
   set_select: function(selected){
        this.select = selected;
        this.trigger('change',this);
   },
   is_select: function(){
        return this.select;
   },
   is_selected_category: function(){
        return this.category_selected;
   },
    });
});
