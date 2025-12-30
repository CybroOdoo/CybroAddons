/** @odoo-module */
import { KanbanRecord } from '@web/views/kanban/kanban_record';
const { onMounted } = owl;
import { onWillDestroy } from "@odoo/owl";
import { registry } from '@web/core/registry';
import { useService, useBus } from "@web/core/utils/hooks";
import { FileViewer } from "@web/core/file_viewer/file_viewer";
// Define a unique identifier for the FileViewer
var fileViewer_id = 1;
// Create a custom class 'DocumentKanbanRecord' that extends 'KanbanRecord'
export class DocumentKanbanRecord extends KanbanRecord {
    setup() {
        super.setup();
        this.containsSelectionOn = false;
        this.orm = useService('orm');
        // Subscribe to custom bus events
        useBus(this.env.bus, 'cancel_button_click', (ev) => this.cancel_button_click());
        useBus(this.env.bus, 'select_button_click', () => this.select_button_click());
        onMounted(() => {
            this.AddClassStyle();
            this.env.bus.trigger('workspace_changed');
        });
        onWillDestroy(() => {
            // Remove event listener and trigger a bus event when destroying the component
            this.__owl__.bdom.el.querySelector('.kanban_document').removeEventListener('click', function (event) {
                if (self.containsSelectionOn) {
                    self.DivSelect(event);
                }
            });
            this.env.bus.trigger('workspace_switched');
        });
    }
    AddClassStyle() {
        // Add a custom class to the element
        this.__owl__.bdom.el.classList.add('document_management_record');
    }
    cancel_button_click() {
        /* Function to make this.containsSelectionOn False */
        this.containsSelectionOn = false;
    }
    select_button_click() {
        /* Function to make this.containsSelectionOn False */
        this.containsSelectionOn = true;
    }
    onGlobalClick(ev) {
        /* Function to call FileOpen class on a global click of Kanban */
        if (this.containsSelectionOn == false) {
            var self = this;
            var record_id = (ev.target.children[0] && ev.target.children[0].getAttribute('data-id')) || ev.target.getAttribute('data-id');
            if (record_id) {
                this.orm.call('document.file', 'get_documents_list', [record_id]).then(function (result) {
                    const attachment = result[0];
                    const attachment_list = result[1];
                    self.FileOpen(attachment, attachment_list);
                });
            }
        }
    }
    FileOpen(file, files = [file]) {
        /* Method to open the file viewer */
        var self = this;
        let id = 1;
        fileViewer_id = `web.file_viewer${id++}`;
        if (!file.isViewable) {
            return;
        }
        if (files.length > 0) {
            const viewableFiles = files.filter((file) => file.isViewable);
            const index = files.findIndex((item) => item.id === file.id);
            registry.category("main_components").add(fileViewer_id, {
                Component: FileViewer,
                props: {
                    files: viewableFiles,
                    startIndex: index,
                    close: self.close
                },
            });
        }
    }
    close() {
        /* Function to remove fileViewer_id from main_components registry */
        registry.category("main_components").remove(fileViewer_id);
    }
}
