/** @odoo-module **/

import { listView } from '@web/views/list/list_view';
import { registry } from "@web/core/registry";
import { SaleOrderLineCompareListRenderer } from "./sale_order_line_compare_list_renderer";
export const saleOrderLineCompareListView = {
    ...listView,
    Renderer: SaleOrderLineCompareListRenderer,
};
//    extending the list renderer
registry.category("views").add("sale_order_line_compare", saleOrderLineCompareListView);
