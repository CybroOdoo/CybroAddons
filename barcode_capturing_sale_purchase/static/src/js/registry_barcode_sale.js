/** @odoo-module **/

var FormView = require('web.FormView');
import { registry } from "@web/core/registry";
import { ComSaleOrderRender } from '@barcode_capturing_sale_purchase/js/sale_barcode';
//JsClassBarcodeSale constant is added to views registry
export const JsClassBarcodeSale = {
   ...FormView,
   Renderer: ComSaleOrderRender,
};
registry.category("views").add("sale_order_barcode", JsClassBarcodeSale);
