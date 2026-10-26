/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {KanbanRenderer} from "@web/views/kanban/kanban_renderer";

/** Grouping fields that only the workflow buttons may change. */
const WORKFLOW_FIELDS = ["stage_id", "pharma_state"];

/**
 * Maintenance requests move through their GMP status with the Start, Mark
 * Completed and QA Verify buttons; the stage only mirrors that status.
 * Dropping a card in another stage column says so instead of failing
 * silently. Reordering within a column, and moving between columns of any
 * other grouping, work as usual.
 */
export class PharmaRequestKanbanRenderer extends KanbanRenderer {
    setup() {
        super.setup();
        this.notification = useService("notification");
    }

    get canMoveRecords() {
        if (WORKFLOW_FIELDS.includes(this.props.list.groupByField?.name)) {
            return this.canResequenceRecords;
        }
        return super.canMoveRecords;
    }

    async sortRecordDrop(dataRecordId, dataGroupId, params) {
        const {element, parent} = params;
        const groupBy = this.props.list.groupByField?.name;
        const changesGroup = parent && parent.dataset.id !== element.parentElement.dataset.id;
        if (this.props.list.isGrouped && WORKFLOW_FIELDS.includes(groupBy) && changesGroup) {
            parent.classList.remove("o_kanban_hover");
            this.notification.add(
                _t("Open the request and use its buttons (Start, Mark Completed, QA Verify) to move it. The stage follows the GMP status."),
                {title: _t("Request not moved"), type: "warning"}
            );
            return;
        }
        return super.sortRecordDrop(...arguments);
    }
}

export const pharmaRequestKanbanView = {
    ...kanbanView,
    Renderer: PharmaRequestKanbanRenderer,
};

registry.category("views").add("pharma_maintenance_request_kanban", pharmaRequestKanbanView);
