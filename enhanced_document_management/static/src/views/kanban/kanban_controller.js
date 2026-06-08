/** @odoo-module */
import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {registry} from '@web/core/registry';
import {CustomKanbanRenderer} from './kanban_renderer'
import {patch} from "@web/core/utils/patch";
const {onMounted} = owl;
import {DocumentKanbanRecord} from './kanban_record'
import {useRef, useState} from "@odoo/owl";
import {kanbanView} from '@web/views/kanban/kanban_view';
import {useService, useBus} from "@web/core/utils/hooks";
import { user } from "@web/core/user";

patch(KanbanController.prototype, {
    /**
     * Setup method
     */
    setup() {
        this.actionService = useService("action");
        this.user = user;
        useBus(this.env.bus, 'searchPanel_toggle', (ev) => this.searchPanelToggle(ev));
        useBus(this.env.bus, 'docs_check_box', (ev) => this._onSelectDocs(ev));
        useBus(this.env.bus, 'searchPanel_toggle', (ev) => this.HideSelectButton());
        this.document_multi_checkbox = useRef("document_multi_checkbox");
        this.lead_button = useRef('create_lead')
        this.task_button = useRef('create_task')
        super.setup();
        this.orm = useService('orm');
        this.userSettings = useService("action")
        this.viewState = useState({
            view_id: null
        })
        onMounted(() => {
            this.ViewLead_ProjectButton()
            this.Workspace_id = 1
            this.Workspace_name = 'All'
            this.HideSelectButton()
            this.documents_selected = [];
            this.containsSelectionOn = false;
        });
    },
    /**
     * method to make create crm and create lead button show and hide if crm and project is installed or not
     */
    async ViewLead_ProjectButton() {
        try {
            var settings_value = await this.orm.call('res.config.settings', 'search_read', [], {fields: ["is_module_crm", "is_module_project"]});
            /**
             * If method
             * @param {any} settings_value.length > 0
             */
            if (settings_value.length > 0) {
                var module_crm = settings_value[settings_value.length - 1]['is_module_crm']
                var module_lead = settings_value[settings_value.length - 1]['is_module_project']
                /**
                 * If method
                 * @param {any} this.lead_button.el
                 */
                if (this.lead_button.el) {
                    this.lead_button.el.style.display = module_crm ? 'block' : 'none';
                }
                /**
                 * If method
                 * @param {any} this.task_button.el
                 */
                if (this.task_button.el) {
                    this.task_button.el.style.display = module_lead ? 'block' : 'none';
                }
            }
        } catch (error) {
            /**
             * If method
             * @param {any} this.lead_button.el
             */
            if (this.lead_button.el) {
                this.lead_button.el.style.display = 'block';
            }
            /**
             * If method
             * @param {any} this.task_button.el
             */
            if (this.task_button.el) {
                this.task_button.el.style.display = 'block';
            }
        }
    },
    /**
     * * method to get workspace_id
     * @param {any} ev
     */
    searchPanelToggle(ev) {
        this.Workspace_id = ev.detail['Id']
        this.Workspace_name = ev.detail['workspace'].display_name
    },
    /**
     * * method to open file upload wizard
     */
    _onUpload() {
        this.actionService.doAction({
            name: "Upload Documents",
            type: 'ir.actions.act_window',
            res_model: 'document.file',
            view_mode: 'form',
            views: [
                [false, 'form']
            ],
            target: 'new',
        })
    },
    /**
     * * Performs an action to add a URL. * Opens a new form view for the 'document.url' model.
     */
    _onAddUrl() {
        this.actionService.doAction({
            'type': 'ir.actions.act_window',
            'name': _t('Add Url'),
            'res_model': 'document.url',
            'view_mode': 'form',
            'target': 'new',
            'views': [
                [false, "form"]
            ],
        });
    },
    /**
     * * Performs an action to request a document. * Opens a new form view for the 'request.document' model.
     */
    async _onRequestDoc() {

        var self = this
        await this.orm.call('request.document', 'get_wizard_view', ['enhanced_document_management.request_document_wizard_view_form']).then(function (result) {
            self.viewState.view_id = result
        })
        this.actionService.doAction({
            'type': 'ir.actions.act_window',
            'name': 'Add Document Request',
            'res_model': 'request.document',
            'view_mode': 'form',
            'target': 'new',
            'views': [[parseInt(self.viewState.view_id) || false, "form"]],
        });
    },
    /**
     * * Performs an action to share a document. * Creates a URL for sharing the selected documents and triggers an action with the result.
     */
    _onShare() {
        var self = this;
        this.orm.call('document.share',
            'create_url',
            [this.documents_selected]).then(function (result) {
            self.actionService.doAction(result);
        });
    },
    /**
     * * Method to Hide Select Button
     */
    HideSelectButton() {
        const self = this;
        const selectDocumentsbutton = this.rootRef.el.querySelectorAll('.select_document');
        const kanbanDocumentsCount = this.rootRef.el.querySelectorAll('.kanban_document').length;
        /**
         * If method
         * @param {any} this.props.resModel
         */
        if (this.props.resModel === 'document.file') {
            this.orm.call('document.file', 'get_document_count', [this.Workspace_id])
                .then(result => {
                    selectDocumentsbutton.forEach((selectDocumentsbutton) => {
                        selectDocumentsbutton.style.display = self.Workspace_name === 'All' ? (result[1] >= 2 ? 'block' : 'none') : (result[0] >= 2 ? 'block' : 'none');
                    });
                });
        }
    },
    /**
     * * method to create task based on selected document
     */
    _onCreateTask() {
        var self = this;
        this.orm.call('document.file', 'action_btn_create_task', [this.documents_selected]).then(function (result) {
            /**
             * If method
             * @param {any} result
             */
            if (result) {
                self.documents_selected = []
                self.actionService.doAction('edm_soft_reload');
            } else {
                self.actionService.doAction({
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': "Install Project Module to use this function",
                        'type': 'info',
                        'sticky': false,
                    }
                })
            }
        });
    },
    /**
     * * method to add selected document in a list
     * @param {any} ev
     */
    _onSelectDocs(ev) {
        var toast = $(this.__owl__.bdom.el).find('.toast')
        var record1 = ev.detail['event']
        var record2 = ev.detail['event'].dataset.content_type
        var record_id = parseInt(ev.detail['event'].dataset.id);
        /**
         * * Handles the logic when a checkbox is checked. * Adds the 'selected' class to parent and sibling elements. * Adds the record ID to the documents_selected array.
         * @param {any} ev.detail['event'].checked
         */
        if (ev.detail['event'].checked) {
            $(ev.detail['event']).closest(".document_management_record").addClass("selected");
            $(ev.detail['event']).closest(".document_table").addClass("selected");
            $(ev.detail['event']).closest(".kanban_document").find('.document_image').addClass("selected");
            $(ev.detail['event']).closest(".kanban_document").addClass("selected");
            $(ev.detail['event']).closest(".kanban_document").find('.document_details').addClass("selected");
            toast.addClass('d-flex');
            this.documents_selected.push(record_id);
        } else {
            /**
             * Handles the logic when a checkbox is unchecked.
             * Removes the 'selected' class from parent and sibling elements.
             * Removes the record ID from the documents_selected array.
             * Removes the 'show' class from the toast element if no more documents are selected.
             */
            $(ev.detail['event']).closest(".document_management_record").removeClass("selected");
            $(ev.detail['event']).closest(".document_table").removeClass("selected");
            $(ev.detail['event']).closest(".kanban_document").find('.document_image').removeClass("selected");
            $(ev.detail['event']).closest(".kanban_document").removeClass("selected");
            $(ev.detail['event']).closest(".kanban_document").find('.document_details').removeClass("selected");
            let index = this.documents_selected.indexOf(record_id);
            this.documents_selected.splice(index, 1)
            /**
             * If method
             * @param {any} this.documents_selected.length
             */
            if (this.documents_selected.length == 0) {
                toast.removeClass('d-flex');
            }
        }
    },
    /**
     * * Method to download selected file as a Zip
     */
    _onDownloadArchive() {
        var self = this;
        /**
         * If method
         * @param {any} this.documents_selected.length > 0
         */
        if (this.documents_selected.length > 0) {
            this.orm.call('document.file', 'download_zip_function', [this.documents_selected]).then(function (res) {
                self.actionService.doAction(res)
            })
        }
    },
    /**
     * * method to archive selected document
     */
    _onArchiveDocument() {
        /**
         * If method
         * @param {any} this.documents_selected.length !
         */
        if (this.documents_selected.length != 0) {
            var self = this;
            this.orm.call('document.file', 'document_file_archive', [this.documents_selected]).then(function (result) {
                self.documents_selected = []
                self.actionService.doAction('edm_soft_reload');
            });
        } else {
            Dialog.alert(this, "Please select least one document");
        }
    },
    /**
     * * method to create lead based on selected document
     */
    _onCreateLead() {
        var self = this;
        this.orm.call('document.file', 'action_btn_create_lead', [this.documents_selected]).then(function (result) {
            /**
             * If method
             * @param {any} result
             */
            if (result) {
                self.documents_selected = []
                self.actionService.doAction('edm_soft_reload');
            } else {
                self.actionService.doAction({
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': "Install CRM Module to use this function",
                        'type': 'info',
                        'sticky': false,
                    }
                })
            }
        });
    },
    /**
     * * method to open email composer
     * @param {any} ev
     */
    _onMailDocument: function (ev) {
        var self = this;
        this.orm.call('document.file', 'on_mail_document', [this.documents_selected]).then(function (result) {
            self.documents_selected = []
            self.actionService.doAction(result);
        });
    },
    /**
     * Oncopydocument method
     */
    _onCopyDocument() {
        var self = this;
        this.user.hasGroup('enhanced_document_management.view_all_document').then(
            (has_group) => {
                /**
                 * If method
                 * @param {any} has_group
                 */
                if (has_group) {
                    self.actionService.doAction({
                        'type': 'ir.actions.act_window',
                        'name': 'copy',
                        'res_model': 'work.space',
                        'view_mode': 'form',
                        'target': 'new',
                        'views': [
                            [false, 'form']
                        ],
                        'context': {
                            'default_doc_ids': this.documents_selected
                        }
                    });
                } else {
                    self.actionService.doAction({
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': "You don't have permission to perform this action",
                            'type': 'danger',
                            'sticky': false,
                        }
                    })
                }
            })
    },
    /**
     * Ondelete method
     * @param {any} ev
     */
    _onDelete(ev) {
        this.user.hasGroup('enhanced_document_management.view_all_document').then(
            (has_group) => {
                /**
                 * If method
                 * @param {any} has_group
                 */
                if (has_group) {
                    var self = this;
                    var record_id = parseInt(ev.target.dataset.id)
                    this.orm.call('document.file', 'document_file_delete', [this.documents_selected]).then(function (result) {
                        self.documents_selected = []
                        self.actionService.doAction('edm_soft_reload');
                    });
                } else {
                    this.actionService.doAction({
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': "You don't have permission to perform this action",
                            'type': 'danger',
                            'sticky': false,
                        }
                    })
                }
            })
    },
    /**
     * Select doc method
     */
    Select_Doc() {
        this.rootRef.el.querySelectorAll('.cancel_btn').forEach(btn => btn.style.display = 'block');
        this.rootRef.el.querySelectorAll('.select_document').forEach(doc => doc.style.display = 'none');
        const elements = this.rootRef.el.querySelectorAll(
            '.on_upload_doc, .dropdown-toggle-split, .o_search_panel_category_value');
        elements.forEach((element) => {
            element.classList.add('disabled');
        });
    },
    /**
     * Cancelselect method
     */
    CancelSelect() {
        this.containsSelectionOn = false
        this.documents_selected = []
        this.rootRef.el.querySelectorAll('.o_kanban_record').forEach((kanban_record) => {
            kanban_record.classList.remove("selection_on")
        });
        this.rootRef.el.querySelectorAll('.selected').forEach((selected_doc) => {
            selected_doc.classList.remove('selected')
        });
        this.rootRef.el.querySelectorAll('.o_search_panel_category_value').forEach((search_panel) => {
            search_panel.classList.remove('disabled')
        });
        this.rootRef.el.querySelectorAll('.toast').forEach(toast => {
            toast.classList.remove('d-flex');
        });
        this.rootRef.el.querySelectorAll('.cancel_btn').forEach(btn => {
            btn.style.display = 'none';
        });
        this.rootRef.el.querySelectorAll('.select_document').forEach(document => document.style.display =
            'block');
        this.rootRef.el.querySelectorAll('.on_upload_doc').forEach(element => {
            element.classList.remove('disabled');
        });
        this.rootRef.el.querySelectorAll('.dropdown-toggle-split').forEach(element => {
            element.classList.remove('disabled');
        });
    }
})
registry.category('views').add('button_in_kanban_view', {
    ...kanbanView,
    Controller: KanbanController,
    Renderer: CustomKanbanRenderer,
});
