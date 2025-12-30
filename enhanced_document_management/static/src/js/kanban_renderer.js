/** @odoo-module */
// Import necessary modules and utilities from Odoo
import { DocumentKanbanRecord } from './kanban_record';
import { KanbanRenderer } from '@web/views/kanban/kanban_renderer';
const { onMounted } = owl;
import { useBus } from "@web/core/utils/hooks";
// Create a custom class 'CustomKanbanRenderer' that extends 'KanbanRenderer'
export class CustomKanbanRenderer extends KanbanRenderer {
    async setup() {
        super.setup(...arguments);
        // Subscribe to custom bus events
        useBus(this.env.bus, 'workspace_switched', (ev) => this.eventListener = false);
        onMounted(() => {
            // Select all elements with class 'select_document' and add click event listeners
            const selectDocumentButtons = this.rootRef.el.ownerDocument.querySelectorAll('.select_document');
            selectDocumentButtons.forEach(button => {
                button.addEventListener('click', event => this.Select_button_click(event, this));
            });
            // Select all elements with class 'cancel_btn' and add click event listeners
            const cancelBtns = this.rootRef.el.ownerDocument.querySelectorAll('.cancel_btn');
            cancelBtns.forEach(btn => {
                btn.addEventListener('click', event => this.cancel_button_click(event, this));
            });
            // Call a function to add CSS styles or classes
            this.AddClassStyle();
            // Set the eventListener property to false
            this.eventListener = false;
        });
    }
    AddClassStyle() {
        // Add custom classes to elements
        this.__owl__.bdom.el.classList.add('o_document_kanban_renderer');
        this.__owl__.bdom.parentEl.classList.add('o_component_with_workspace_panel');
    }
    Select_button_click(ev) {
        /**
         * Handles the click event of the 'Select' button. Adds a CSS class to kanban records
         * and sets up event listeners for clicking on 'kanban_document' elements if not already done.
         * Triggers a custom event 'select_button_click' on the component's event bus.
         *
         * @param {Event} ev - The click event.*/
        var self = this;
        this.__owl__.bdom.el.querySelectorAll('.o_kanban_record').forEach((kanban_record) => {
            kanban_record.classList.add("selection_on");
            self.containsSelectionOn = true;
        });
        if (!this.eventListener) {
            this.__owl__.bdom.el.querySelectorAll('.kanban_document').forEach((selection_on_div) => {
                selection_on_div.addEventListener('click', function (event) {
                    if (self.containsSelectionOn) {
                        self.DivSelect(event);
                    }
                });
            });
            this.eventListener = true;
        }
        this.env.bus.trigger('select_button_click');
    }
    cancel_button_click() {
        /**
         * Handles the click event of the 'Cancel' button. Resets the selection state and
         * triggers a custom event 'cancel_button_click' on the component's event bus.
         */
        this.containsSelectionOn = false;
        this.env.bus.trigger('cancel_button_click');
    }
    DivSelect(event) {
        /**
         * Handles the click event on a 'kanban_document' element within a selection context.
         * Toggles the checked state of a checkbox element within the clicked element and triggers
         * a custom event 'docs_check_box' on the component's event bus.
         *
         * @param {Event} event - The click event on the 'kanban_document' element.
         */
        event.preventDefault();
        if (this.containsSelectionOn) {
            const checkboxElement = event.currentTarget.querySelector('.docs_check_box');
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
// Extend the components of CustomKanbanRenderer to include DocumentKanbanRecord
CustomKanbanRenderer.components = {
    ...KanbanRenderer.components,
    KanbanRecord: DocumentKanbanRecord,
};
