/** @odoo-module */

import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { useRef } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.select_uom = useRef("uom_value");
    },
});
Orderline.props = {
    ...Orderline.props,
    line: {
        shape: {
            resetUom: { type: Function, optional: true },
            getUom: { type: Function, optional: true },
            onSelectionChangedUom: { type: Function, optional: true },
        },
    },
};
