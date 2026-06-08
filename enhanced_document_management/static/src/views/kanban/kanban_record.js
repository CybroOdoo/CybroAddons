/** @odoo-module */
import { KanbanRecord } from '@web/views/kanban/kanban_record';
import { onWillDestroy } from "@odoo/owl";
import { registry } from '@web/core/registry';
const { onMounted } = owl;
import { useService, useBus } from "@web/core/utils/hooks";
import { FileViewer } from "@web/core/file_viewer/file_viewer";
var fileViewer_id = 1;

function normalizeViewerFile(file) {
    if (!file) {
        return file;
    }
    return {
        ...file,
        name: file.name || file.displayName || file.filename || "",
    };
}

export class DocumentKanbanRecord extends KanbanRecord {
    /**
     * Setup method
     */
    setup() {
        super.setup();
        this.containsSelectionOn = false;
        this.orm = useService('orm');
        this.actionService = useService('action');
        this.notification = useService('notification');
        useBus(this.env.bus, 'cancel_button_click', (ev) => this.cancel_button_click());
        useBus(this.env.bus, 'select_button_click', () => this.select_button_click());
        onMounted(() => {
            this.AddClassStyle();
            this.env.bus.trigger('workspace_changed');
        });
        onWillDestroy(() => {
            // Remove event listener and trigger a bus event when destroying the component
            this.__owl__.bdom.el.querySelector('.kanban_document').removeEventListener('click', function (event) {
                /**
                 * If method
                 * @param {any} self.containsSelectionOn
                 */
                if (self.containsSelectionOn) {
                    self.DivSelect(event);
                }
            });
            this.env.bus.trigger('workspace_switched');
        });
    }
    /**
     * Add a custom class to the element
     */
    AddClassStyle() {
        this.__owl__.bdom.el.classList.add('document_management_record');
    }
    /**
     * Function to make this.containsSelectionOn False
     */
    cancel_button_click() {
        this.containsSelectionOn = false;
    }
    /**
     * Function to make this.containsSelectionOn False
     */
    select_button_click() {
        this.containsSelectionOn = true;
    }
    /**
     * Function to call FileOpen class on a global click of Kanban
     * @param {any} ev
     */
    onGlobalClick(ev) {
        /**
         * If method
         * @param {any} this.containsSelectionOn
         */
        if (this.containsSelectionOn == false) {
            var self = this;
            var recordEl = ev.target.closest('[data-id]');
            var record_id = recordEl ? recordEl.getAttribute('data-id') : null;
            if (record_id) {
                this.orm.call('document.file', 'get_documents_list', [record_id]).then(function (result) {
                    const attachment = result[0];
                    const attachment_list = result[1];
                    if (attachment.is_locked) {
                        self.orm.call('document.file', 'action_click_open_locked', [attachment.id]).then(function (action) {
                            self.actionService.doAction(action);
                        });
                        return;
                    }
                    self.FileOpen(attachment, attachment_list);
                });
            }
        }
    }
    /**
     * Fileopen method
     * @param {any} file
     * @param {any} files
     */
    FileOpen(file, files = [file]) {
        var self = this;
        let id = 1;
        fileViewer_id = `web.file_viewer${id++}`;
        const normalizedFile = normalizeViewerFile(file);
        const normalizedFiles = files.map(normalizeViewerFile);
        /**
         * If method
         * @param {any} !file.isViewable
         */
        if (!normalizedFile?.isViewable) {
            const downloadUrl = normalizedFile.downloadUrl || normalizedFile.defaultSource || `/web/content/${normalizedFile.id}?download=true`;
            window.open(downloadUrl, '_blank');
            return;
        }
        /**
         * If method
         * @param {any} files.length > 0
         */
        if (normalizedFiles.length > 0) {
            const viewableFiles = normalizedFiles.filter((viewerFile) => viewerFile?.isViewable);
            const index = viewableFiles.findIndex((item) => item.id === normalizedFile.id);
            if (!viewableFiles.length || index < 0) {
                const downloadUrl = normalizedFile.downloadUrl || normalizedFile.defaultSource || `/web/content/${normalizedFile.id}?download=true`;
                window.open(downloadUrl, '_blank');
                return;
            }
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
    /**
     * Close method
     */
    close() {
        registry.category("main_components").remove(fileViewer_id);
    }
}
