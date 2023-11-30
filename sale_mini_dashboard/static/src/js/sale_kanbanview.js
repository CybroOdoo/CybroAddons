/** @odoo-module **/
import { registry } from "@web/core/registry";
import { kanbanView } from '@web/views/kanban/kanban_view';
import { KanbanRenderer } from '@web/views/kanban/kanban_renderer';
import { SaleDashBoard } from '@sale_mini_dashboard/js/sale_dashboard';

/**
 * Sale Dashboard Kanban Renderer class, extending the base KanbanRenderer.
 * @extends KanbanRenderer
 */
export class SaleDashBoardKanbanRenderer extends KanbanRenderer {};

// Template for the SaleDashBoardKanbanRenderer component
SaleDashBoardKanbanRenderer.template = 'sale_mini_dashboard.SaleKanbanView';

// Components used by SaleDashBoardKanbanRenderer
SaleDashBoardKanbanRenderer.components = Object.assign({}, KanbanRenderer.components, { SaleDashBoard });

/**
 * Sale Dashboard Kanban View configuration.
 * @type {Object}
 */
export const SaleDashBoardKanbanView = {
    ...kanbanView,
    // Use the custom SaleDashBoardKanbanRenderer as the renderer for the kanban view
    Renderer: SaleDashBoardKanbanRenderer,
};

// Register the Sale Dashboard Kanban View in the "views" category of the registry
registry.category("views").add("sale_dashboard_kanban", SaleDashBoardKanbanView);
