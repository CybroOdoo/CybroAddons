odoo.define("merge_products_pos.products", function (require) {
    "use strict";
    var pos_screen = require('point_of_sale.screens');

    pos_screen.ProductScreenWidget.include({
        click_product: function(product) {
           if(product.to_weight && this.pos.config.iface_electronic_scale){
               this.gui.show_screen('scale',{product: product});
           }else{
               var self = this;
               var order = self.pos.get_order();
               var lines = order.orderlines.models;
               var flag = false;
               for (var i in lines){
                   if(lines[i].product.display_name == product.display_name){
                       var qty = lines[i].get_quantity();
                       lines[i].set_quantity(qty+1);
                       flag = true;
                   }
               }
               if (!flag){
                   order.add_product(product);
               }
           }
        },
    });
});
