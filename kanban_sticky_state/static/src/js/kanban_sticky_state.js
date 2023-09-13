/** @odoo-module **/
/**
 * KanbanRenderer with Kanban Sticky State
 *
 * This patch modifies the setup method of the component prototype to add functionality
 * related to the Kanban view. It also adds two additional methods, add_class and
 * remove_class, which are called based on the value of session.kanban_sticky_state
 * to add or remove a CSS class from certain elements.
 */
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import session from 'web.session';
import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";
import { useSortable } from "@web/core/utils/sortable";
import { useBus, useService } from "@web/core/utils/hooks";
import { useBounceButton } from "@web/views/view_hook";
import { useState, useRef, onPatched, onWillPatch, onWillDestroy, onMounted } from "@odoo/owl";
function validateColumnQuickCreateExamples(data) {
    const { allowedGroupBys = [], examples = [] } = data;
    if (!allowedGroupBys.length) {
        throw new Error("The example data must contain an array of allowed groupbys");
    }
    if (!examples.length) {
        throw new Error("The example data must contain an array of examples");
    }
}
patch(KanbanRenderer.prototype, 'kanban_sticky_state.KanbanRenderer',{
    /**
     * Setup method for the KanbanRenderer.
     */
      updateStickyHeaderClass() {
        var elements = document.querySelectorAll('.o_kanban_header, .o_column_quick_create, .o_quick_create_folded');
    for (var element of elements) {
        if (session.is_kanban_sticky_state) {
            element.classList.add("is_kanban_sticky_state");
        } else {
            element.classList.remove("is_kanban_sticky_state");
        }
    }
},
    setup() {
        this.dialogClose = [];
        this.state = useState({
            columnQuickCreateIsFolded:
                !this.props.list.isGrouped || this.props.list.groups.length > 0,
        });
        this.dialog = useService("dialog");
        this.exampleData = registry
            .category("kanban_examples")
            .get(this.props.archInfo.examples, null);
        if (this.exampleData) {
            validateColumnQuickCreateExamples(this.exampleData);
        }
        this.ghostColumns = this.generateGhostColumns();
        onMounted(() => this.updateStickyHeaderClass());
        onPatched(() => this.updateStickyHeaderClass());
        // Sortable
        let dataRecordId;
        let dataGroupId;
        const rootRef = useRef("root");
        if (this.canUseSortable) {
            useSortable({
                enable: () => this.canResequenceRecords,
                // Params
                ref: rootRef,
                elements: ".o_record_draggable",
                ignore: ".dropdown",
                groups: () => this.props.list.isGrouped && ".o_kanban_group",
                connectGroups: () => this.canMoveRecords,
                cursor: "move",
                // Hooks
                onDragStart: (params) => {
                    const { element, group } = params;
                    dataRecordId = element.dataset.id;
                    dataGroupId = group && group.dataset.id;
                    return this.sortStart(params);
                },
                onDragEnd: (params) => this.sortStop(params),
                onGroupEnter: (params) => this.sortRecordGroupEnter(params),
                onGroupLeave: (params) => this.sortRecordGroupLeave(params),
                onDrop: (params) => this.sortRecordDrop(dataRecordId, dataGroupId, params),
            });
            useSortable({
                enable: () => this.canResequenceGroups,
                // Params
                ref: rootRef,
                elements: ".o_group_draggable",
                handle: ".o_column_title",
                cursor: "move",
                // Hooks
                onDragStart: (params) => {
                    const { element } = params;
                    dataGroupId = element.dataset.id;
                    return this.sortStart(params);
                },
                onDragEnd: (params) => this.sortStop(params),
                onDrop: (params) => this.sortGroupDrop(dataGroupId, params),
            });
        }
        useBounceButton(rootRef, (clickedEl) => {
            if (!this.props.list.count || this.props.list.model.useSampleModel) {
                return clickedEl.matches(
                    [
                        ".o_kanban_renderer",
                        ".o_kanban_group",
                        ".o_kanban_header",
                        ".o_column_quick_create",
                        ".o_view_nocontent_smiling_face",
                    ].join(", ")
                );
            }
            return false;
        });
        onWillDestroy(() => {
            this.dialogClose.forEach((close) => close());
        });
        if (this.env.searchModel) {
            useBus(this.env.searchModel, "focus-view", () => {
                const { model } = this.props.list;
                if (model.useSampleModel || !model.hasData()) {
                    return;
                }
                const firstCard = rootRef.el.querySelector(".o_kanban_record");
                if (firstCard) {
                    // Focus first kanban card
                    firstCard.focus();
                }
            });
        }
        useHotkey(
            "Enter",
            ({ target }) => {
                if (!target.classList.contains("o_kanban_record")) {
                    return;
                }
                // Open first link
                const firstLink = target.querySelector(".oe_kanban_global_click, a, button");
                if (firstLink && firstLink instanceof HTMLElement) {
                    firstLink.click();
                }
                return;
            },
            { area: () => rootRef.el }
        );
        const arrowsOptions = { area: () => rootRef.el, allowRepeat: true };
        if (this.env.searchModel) {
            useHotkey(
                "ArrowUp",
                ({ area }) => {
                    if (!this.focusNextCard(area, "up")) {
                        this.env.searchModel.trigger("focus-search");
                    }
                },
                arrowsOptions
            );
        }
        useHotkey("ArrowDown", ({ area }) => this.focusNextCard(area, "down"), arrowsOptions);
        useHotkey("ArrowLeft", ({ area }) => this.focusNextCard(area, "left"), arrowsOptions);
        useHotkey("ArrowRight", ({ area }) => this.focusNextCard(area, "right"), arrowsOptions);
        let previousScrollTop = 0;
        onWillPatch(() => {
            previousScrollTop = rootRef.el.scrollTop;
        });
        onPatched(() => {
            rootRef.el.scrollTop = previousScrollTop;
        });
        // Add or remove CSS class based on the value of kanban_sticky_state
        if (session.is_kanban_sticky_state) {
            onMounted(this.add_class)
        } else {
            onMounted(this.remove_class)
        }
    },
    /**
     * Add CSS class on condition of kanban_sticky_state value.
     */
    add_class(){
        var elements = document.getElementsByClassName('o_kanban_header')
        for(var element=0;element<elements.length; element++){
            elements[element].classList.add("is_kanban_sticky_state");
        }
    },
    /**
     * Remove CSS class on condition of kanban_sticky_state value.
     */
    remove_class(){
        var elements = document.getElementsByClassName('o_kanban_header')
        for(var element=0;element<elements.length; element++){
                elements[element].classList.remove("is_kanban_sticky_state");
        }
    }
});
