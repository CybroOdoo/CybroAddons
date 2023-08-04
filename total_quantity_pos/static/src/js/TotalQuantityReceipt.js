odoo.define('total_quantity_pos.receipt', function (require) {
"use strict";
   var { Order } = require('point_of_sale.models');
   var Registries = require('point_of_sale.Registries');

   const ReceiptQuant = (Order) => class ReceiptQuant extends Order {
       export_for_printing() {

       // get the total items and total quantities of products
       // by supering the export for printing function.

       var result = super.export_for_printing(...arguments);
       var self = this;
       var total_items = this.orderlines.length;
       let quant_count = 0;
       let i =0 ;
       for( ; i < total_items; ){
       quant_count += this.orderlines[i].quantity
       i++;
       }
        result.total_quantity = quant_count
        return result;
   }
   }
       Registries.Model.extend(Order, ReceiptQuant);
   });
