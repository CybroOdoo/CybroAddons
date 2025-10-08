/** @odoo-module **/

import { formView } from '@web/views/form/form_view';
import { registry } from "@web/core/registry";
import { ComSaleOrderRender } from '@barcode_capturing_sale_purchase/js/sale_barcode';
//JsClassBarcodeSale constant is added to views registry
export const JsClassBarcodeSale = {
   ...formView,
   Renderer: ComSaleOrderRender,
};
registry.category("views").add("sale_order_barcode", JsClassBarcodeSale);
