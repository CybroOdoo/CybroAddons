/** @odoo-module */
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

patch(Order.prototype, {
       setup(){
       super.setup(...arguments);
       },
       export_for_printing() {
           const result = super.export_for_printing(...arguments);
          result.count = this.orderlines.length
          this.receipt = result.count
          var sum = 0;
          this.orderlines.forEach(function(t) {
                    sum += t.quantity;
                })
                result.sum = sum
                return result;
       },
});