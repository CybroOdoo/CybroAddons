/** @odoo-module */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
  /**
     * This file extends the POS receipt functionality
     * to include order type information in the receipt view.
  */
  export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        if (this.order_type_id?.name) {
            result.orderType = this.order_type_id.name;
        }
        return result;
  },
});
