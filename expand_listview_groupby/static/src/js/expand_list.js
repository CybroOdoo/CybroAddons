/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useService } from "@web/core/utils/hooks";
/**
 * patched the ListRenderer for adding the expansion function
 */
patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        this.action = useService("action");
    },
 /**
 * Checking the group if it is folded or not and then expanding correspondingly
 */
    expandFolded(group) {
        if (group.isFolded) {
            this.toggleGroup(group)
        } else {
            if(group.list.groups){
            group.list.groups.forEach((group) => {
                this.expandFolded(group);
            });
            }
        }
    },
 /**
 * function onListExpandData is defined inside the ListRenderer
 */
    onListExpandData() {
        if (this.__owl__.props.list.groupBy.length == 0) {
            this.action.doAction({
                type: "ir.actions.client",
                tag: "display_notification",
                params: {
                    title: "GroupBy",
                    message: "Affects on GroupBy records",
                    sticky: false,
                },
            });
        } else {
            /**
            * calling expandFolded function for check and expand the groupBy(there may be more than one groupBy)
            */
            this.props.list.groups.forEach((group) => {
                this.expandFolded(group);
            })
        }
    },
});
