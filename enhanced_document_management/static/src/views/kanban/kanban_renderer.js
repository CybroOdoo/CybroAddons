/** @odoo-module */
// Import necessary modules and utilities from Odoo
import { DocumentKanbanRecord } from './kanban_record';
import { KanbanRenderer } from '@web/views/kanban/kanban_renderer';
const { onMounted } = owl;
import { useBus } from "@web/core/utils/hooks";
export class CustomKanbanRenderer extends KanbanRenderer {
    /**
     * Setup method
     */
    async setup() {
        super.setup(...arguments);
        useBus(this.env.bus, 'workspace_switched', (ev) => this.eventListener = false);
        onMounted(() => {
            const selectDocumentButtons = this.rootRef.el.ownerDocument.querySelectorAll('.select_document');
            selectDocumentButtons.forEach(button => {
                button.addEventListener('click', event => this.Select_button_click(event, this));
            });
            const cancelBtns = this.rootRef.el.ownerDocument.querySelectorAll('.cancel_btn');
            cancelBtns.forEach(btn => {
                btn.addEventListener('click', event => this.cancel_button_click(event, this));
            });
            this.AddClassStyle();
            this.eventListener = false;
        });
    }
    /**
     * Addclassstyle method
     */
    AddClassStyle() {
        this.__owl__.bdom.el.classList.add('o_document_kanban_renderer');
        this.__owl__.bdom.parentEl.classList.add('o_component_with_workspace_panel');
    }
    /**
     * Select button click method
     * @param {any} ev
     */
    Select_button_click(ev) {
        var self = this;
        this.__owl__.bdom.el.querySelectorAll('.o_kanban_record').forEach((kanban_record) => {
            kanban_record.classList.add("selection_on");
            self.containsSelectionOn = true;
        });
        /**
         * If method
         * @param {any} !this.eventListener
         */
        if (!this.eventListener) {
            this.__owl__.bdom.el.querySelectorAll('.kanban_document').forEach((selection_on_div) => {
                selection_on_div.addEventListener('click', function (event) {
                    /**
                     * If method
                     * @param {any} self.containsSelectionOn
                     */
                    if (self.containsSelectionOn) {
                        self.DivSelect(event);
                    }
                });
            });
            this.eventListener = true;
        }
        this.env.bus.trigger('select_button_click');
    }
    /**
     * Cancel button click method
     */
    cancel_button_click() {
        this.containsSelectionOn = false;
        this.env.bus.trigger('cancel_button_click');
    }
    /**
     * Divselect method
     * @param {any} event
     */
    DivSelect(event) {
        event.preventDefault();
        /**
         * If method
         * @param {any} this.containsSelectionOn
         */
        if (this.containsSelectionOn) {
            const checkboxElement = event.currentTarget.querySelector('.docs_check_box');
            /**
             * If method
             * @param {any} checkboxElement
             */
            if (checkboxElement) {
                const isChecked = !checkboxElement.checked;
                checkboxElement.checked = isChecked;
                const eventData = {
                    event: checkboxElement,
                    self: this,
                    clickEvent: event
                };
                this.env.bus.trigger("docs_check_box", eventData);
            }
        }
    }
}
CustomKanbanRenderer.components = {
    ...KanbanRenderer.components,
    KanbanRecord: DocumentKanbanRecord,
};
