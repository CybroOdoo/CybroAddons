/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
       async processServerData(data) {
          super.processServerData(...arguments);
          this.stock_quant = this.data.models['stock.quant'].getAll();
          this.product_product = this.data.models['product.product'].getAll();
          this.product_template = this.data.models['product.template'].getAll();
       }
})