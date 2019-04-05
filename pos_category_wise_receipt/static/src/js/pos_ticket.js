odoo.define('pos_category_wise_receipt.receipt', function (require) {
"use strict";
var models = require('point_of_sale.models');
var orderline_id = 1;


var order = models.Orderline.extend({

   initialize: function(attr,options){
        console.log("dfdd")
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
        this.id = orderline_id++;
   },
   get_category : function(){
        var product = this.product.pos_categ_id[1];
        return (product ? this.product.pos_categ_id[1] : undefined) || 'UnCategorised Product';
//        return this.product.pos_categ_id[1];
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
    models.Orderline = order;
    return order;
});