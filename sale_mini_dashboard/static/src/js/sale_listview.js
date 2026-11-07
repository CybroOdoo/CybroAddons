import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { SaleDashBoard } from "@sale_mini_dashboard/js/sale_dashboard";

/**
 * List renderer showing the mini dashboard.
 * @extends ListRenderer
 */
export class SaleDashBoardListRenderer extends ListRenderer {
    static template = "sale_mini_dashboard.SaleListView";
    static components = { ...ListRenderer.components, SaleDashBoard };
}

export const SaleDashBoardListView = {
    ...listView,
    Renderer: SaleDashBoardListRenderer,
};

registry.category("views").add("sale_mini_dashboard_list", SaleDashBoardListView);
