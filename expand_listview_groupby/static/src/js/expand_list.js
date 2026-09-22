/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";

patch(ListController.prototype, {
    get isAllExpanded() {
        const list = this.model && this.model.root;
        if (!list || !list.groups || list.groups.length === 0) {
            return false;
        }
        const checkExpanded = (groups) => {
            for (const group of groups) {
                if (group.isFolded) {
                    return false;
                }
                if (group.list && group.list.groups && group.list.groups.length > 0) {
                    if (!checkExpanded(group.list.groups)) {
                        return false;
                    }
                }
            }
            return true;
        };
        return checkExpanded(list.groups);
    },
    expandFolded(group) {
        if (group.isFolded) {
            if (this.toggleGroup) {
                this.toggleGroup(group);
            } else if (group.toggle) {
                group.toggle();
            }
        }
        if (group.list && group.list.groups) {
            group.list.groups.forEach((g) => {
                this.expandFolded(g);
            });
        }
    },
    collapseExpanded(group) {
        if (!group.isFolded) {
            if (this.toggleGroup) {
                this.toggleGroup(group);
            } else if (group.toggle) {
                group.toggle();
            }
        }
        if (group.list && group.list.groups) {
            group.list.groups.forEach((g) => {
                this.collapseExpanded(g);
            });
        }
    },
    onListExpandData() {
        const list = this.model && this.model.root;
        const actionService = this.actionService || this.env.services.action;
        if (!list || !list.groupBy || list.groupBy.length === 0) {
            actionService.doAction({
                type: "ir.actions.client",
                tag: "display_notification",
                params: {
                    title: "GroupBy",
                    message: "Affects on GroupBy records",
                    sticky: false,
                },
            });
        } else {
            if (list.groups) {
                const shouldCollapse = this.isAllExpanded;
                list.groups.forEach((group) => {
                    if (shouldCollapse) {
                        this.collapseExpanded(group);
                    } else {
                        this.expandFolded(group);
                    }
                });
            }
        }
    },
});
