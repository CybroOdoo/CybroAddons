/** @odoo-module **/

import { Orderline } from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';

export const PosMultiVariantOrderline = (Orderline) => class PosMultiVariantOrderline extends Orderline {
    constructor(obj, options) {
        super(...arguments);
        this.product_variants = this.product_variants || [];
    }
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.product_variants = this.product_variants || [];
        return json;
    }
    export_for_printing() {
        var line = super.export_for_printing(...arguments);
        line.product_variants = this.product_variants;
        return line;
    }
}

Registries.Model.extend(Orderline, PosMultiVariantOrderline);
