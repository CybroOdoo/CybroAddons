/** @odoo-module **/
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { StockPickingDashboard } from './stock_picking_dashboard.js';
/**
 * Custom renderer that includes the StockPickingDashboard component.
 */
export class StockPickingDashboardRenderer extends ListRenderer {};

StockPickingDashboardRenderer.template = 'stock.StockPickingListView';
StockPickingDashboardRenderer.components= Object.assign({}, ListRenderer.components, {StockPickingDashboard})
export const StockPickingListView = {
    ...listView,
    Renderer: StockPickingDashboardRenderer,
};
registry.category("views").add("stock_picking_dashboard_list", StockPickingListView);
