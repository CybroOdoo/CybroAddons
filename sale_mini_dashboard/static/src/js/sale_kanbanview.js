import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { SaleDashBoard } from "@sale_mini_dashboard/js/sale_dashboard";

/**
 * Kanban renderer showing the mini dashboard above the records.
 * @extends KanbanRenderer
 */
export class SaleDashBoardKanbanRenderer extends KanbanRenderer {
    static template = "sale_mini_dashboard.SaleKanbanView";
    static components = { ...KanbanRenderer.components, SaleDashBoard };
}

export const SaleDashBoardKanbanView = {
    ...kanbanView,
    Renderer: SaleDashBoardKanbanRenderer,
};

// The key is prefixed with the module name: Odoo 20 core already registers
// "sale_dashboard_kanban" and "sale_dashboard_list".
registry.category("views").add("sale_mini_dashboard_kanban", SaleDashBoardKanbanView);
