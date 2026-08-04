/** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder, {
    extraFields: {
        ...(PosOrder.extraFields || {}),
        refunded_order_id: {
            model: "pos.order",
            name: "refunded_order_id",
            relation: "pos.order",
            type: "many2one",
        },
    },
});
