/** @odoo-module */
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {registry} from '@web/core/registry';
import {useEffect} from "@odoo/owl";

export class BarcodeKanbanController extends KanbanController {
    static template = "BarcodeKanbanController";

    setup() {
        super.setup();
        useEffect(() => {
            this.env.bus.trigger("TOGGLE_NAVBAR:HIDE", {show: false})
            return () => {
                this.env.bus.trigger("TOGGLE_NAVBAR:HIDE", {show: true})
            }
        })
    }

    handleGoBack() {
        window.history.go(-1)
    }
}

export const barcodeKanbanView = {
    ...kanbanView,
    Controller: BarcodeKanbanController,
}
registry.category("views").add("barcode_kanban", barcodeKanbanView);
