/** @odoo-module **/
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { StockMoveDashboard } from './stock_move_dashboard.js';
/**
 * A renderer for the stock move dashboard list view.
 */
export class StockMoveDashboardRenderer extends ListRenderer {};

StockMoveDashboardRenderer.template = 'stock.StockMoveListView';
StockMoveDashboardRenderer.components= Object.assign({}, ListRenderer.components, {StockMoveDashboard})
export const StockMoveListView = {
    ...listView,
    Renderer: StockMoveDashboardRenderer,
};
registry.category("views").add("stock_move_dashboard_list", StockMoveListView);
