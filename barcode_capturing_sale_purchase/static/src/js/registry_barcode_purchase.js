/** @odoo-module **/

import { formView } from '@web/views/form/form_view';
import { registry } from "@web/core/registry";
import { ComPurchaseOrderRender } from '@barcode_capturing_sale_purchase/js/purchase_barcode';
//JsClassBarcodePurchase constant is added to views registry
export const JsClassBarcodePurchase = {
   ...formView,
   Renderer: ComPurchaseOrderRender,
};
registry.category("views").add("purchase_order_barcode", JsClassBarcodePurchase);
