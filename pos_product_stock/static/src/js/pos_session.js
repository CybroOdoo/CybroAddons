/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
       async processServerData(data) {
          super.processServerData(...arguments);
        this.res_setting = this.data.models['res.config.settings'].getFirst();
        this.stock_quant = this.data.models['stock.quant'].getAll()
        this.move_line = this.data.models['stock.move.line'].getAll();
        this.product_product = this.data.models['product.product'].getAll();
       }
})