odoo.define('document.uploadButton', function(require) {
   "use strict";
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var _t = core._t;
    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');
    var viewRegistry = require('web.view_registry');
    var DocumentSearchPanel = require('document.search_panel');
    var rpc = require('web.rpc');
    const session = require('web.session');

    /**
        * Extending KanbanController to add custom functions
    */
    var KanbanButton = KanbanController.extend({
    buttons_template: 'button_in_kanban.button',
    events: _.extend({}, KanbanController.prototype.events, {
       'click .on_upload_doc': '_onUpload',
       'click .on_delete_button': '_onDelete',
       'click .on_share_button': '_onShare',
       'click .on_add_url': '_onAddUrl',
       'click .docs_check_box': '_onSelectDocs',
       'click .on_download_archive': '_onDownloadArchive',
       'click .on_archive_document': '_onArchiveDocument',
       'click .on_mail_document': '_onMailDocument',
       'click .on_copy_document': '_onCopyDocument',
       'click .on_create_task': '_onCreateTask',
       'click .on_create_lead': '_onCreateLead',
       'click .on_add_request': '_onRequestDoc',
    }),
    documents_selected: [],
    _onMailDocument:function(ev){
        /**
            * Method to open email composer
        */
       var self = this;
       rpc.query({
            model: 'document.file',
            method: 'on_mail_document',
            args: [this.documents_selected],
            }).then(function (result){
                self.documents_selected = []
                self.do_action(result);
            });
       },
    _onCopyDocument:function(ev){
        /**
            * Method to open copy/cut wizard
        */
        session.user_has_group('enhanced_document_management.document_management_group_manager').then(
            (has_group) => {
                if (has_group){
                    this.do_action({
                        'type': 'ir.actions.act_window',
                        'name': 'copy',
                        'res_model': 'document.tool',
                        'view_mode': 'form',
                        'target': 'new',
                        'views': [[false, 'form']],
                        'context': {
                            'default_doc_ids': this.documents_selected
                        }
                    });
                }else{
                    this.do_action({
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
    _onRequestDoc:function(ev){
        /**
            * Method to open document request wizard
        */
        this.do_action({
            'type': 'ir.actions.act_window',
            'name': 'Add Document Request',
            'res_model': 'request.document',
            'view_mode': 'form',
            'target': 'new',
            'views': [[false, "form"]],
            'context': {
                'default_workspace_id': this.searchModel.get('selectedWorkspaceId')
            }
        });
    },
    _onArchiveDocument: function(ev){
        /**
            * Method to archive selected document
        */
        if (this.documents_selected.length != 0){
            var self = this;
            rpc.query({
                model: 'document.file',
                method: 'document_file_archive',
                args: [this.documents_selected],
            }).then(function (result){
                self.documents_selected = []
                location.reload();
            });
        }else{
            Dialog.alert(this, "Please select least one document");
        }
    },
    _onSelectDocs: function(ev){
        /**
            * Method to add selected document in a lisk
        */
        var self = this;
        var toast = self.$el.find('.toast')
        var record_id =parseInt(ev.target.dataset.id);
        if (ev.target.checked){
            self.$el.find('.o_legacy_kanban_view')[0].style.maxWidth = "82%";
            toast.addClass('show');
            this.documents_selected.push(record_id);
        }
        else{
            let index = this.documents_selected.indexOf(record_id);
            this.documents_selected.splice(index, 1)
            if ( this.documents_selected.length == 0){
                self.$el.find('.o_legacy_kanban_view')[0].style.maxWidth = "100%";
                toast.removeClass('show');
            }
        }
    },
    _onDownloadArchive: function(ev){
        /**
            * Method to download selected file as a Zip
        */
        var self = this;
        if (this.documents_selected.length > 0) {
            rpc.query({
                model: 'document.file',
                method: 'archive_function',
                args: [this.documents_selected]
            }).then(function(res){
                self.do_action(res)
            })
        }
    },
    _onAddUrl: function(){
        /**
            * Method to open add URL wizard
        */
        return this.do_action({
            'type': 'ir.actions.act_window',
            'name': _('Add Url'),
            'res_model': 'document.url',
            'view_mode': 'form',
            'target': 'new',
            'views': [[false, "form"]],
            'context': {
                'default_workspace_id': this.searchModel.get('selectedWorkspaceId'),
            }
        });
    },
    _onCreateTask: function(){
        /**
            * Method to create task based on selected document
        */
        var self = this;
        rpc.query({
            model: 'document.file',
            method: 'action_btn_create_task',
            args: [this.documents_selected]
        }).then(function (result){
            if (result) {
                self.documents_selected = []
                location.reload();
            }
            else {
                self.do_action({
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
    _onCreateLead: function(){
        /**
            * Method to create lead based on selected document
        */
        var self = this;
        rpc.query({
            model: 'document.file',
            method: 'action_btn_create_lead',
            args: [this.documents_selected]
        }).then(function (result){
            if (result) {
                self.documents_selected = []
                location.reload();
            }else {
                self.do_action({
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
    _onDelete: function(ev){
        /**
            * Method to delete selected records
        */
        session.user_has_group('enhanced_document_management.document_management_group_manager').then(
            (has_group) => {
                if (has_group){
                    var self = this;
                    var record_id = parseInt(ev.target.dataset.id)
                    rpc.query({
                        model: 'document.file',
                        method: 'document_file_delete',
                        args: [this.documents_selected],
                    }).then(function (result){
                        self.documents_selected = []
                        location.reload();
                    });
                }else{
                    this.do_action({
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
    _onShare: function(ev){
        /**
            * Method to create sharable url based on selected document
        */
        var self = this;
        rpc.query({
            model: 'document.share',
            method: 'create_url',
            args: [this.documents_selected],
        }).then(function (result){
            self.do_action(result)
        });
    },
    _onUpload: function(){
        /**
            * Method to open file upload wizard
        */
        this.do_action({
            name: "Upload Documents",
            type: 'ir.actions.act_window',
            res_model: 'document.file',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_workspace_id: this.searchModel.get('selectedWorkspaceId'),
                default_content_type: 'file',
            },
        })
    },
    updateButtons() {
        /**
            * Method to restrict button click
        */
        const selectedWorkspaceId = this.searchModel.get('selectedWorkspaceId');
        this.$buttons.find('.on_upload_doc').prop('disabled', !selectedWorkspaceId);
        this.$buttons.find('.on_add_url').prop('disabled', !selectedWorkspaceId);
        this.$buttons.find('.on_add_request').prop('disabled', !selectedWorkspaceId);
       },

    });
    var DocumentKanbanView = KanbanView.extend({
       config: _.extend({}, KanbanView.prototype.config, {
           Controller: KanbanButton,
           SearchPanel: DocumentSearchPanel,
       }),
    });
    viewRegistry.add('button_in_kanban_view', DocumentKanbanView);
    Dialog.link = function (owner, message, options) {
        var buttons = [{
            text: _t("Ok"),
            close: true,
            click: options && options.confirm_callback,
        }];
        return new Dialog(owner, _.extend({
            size: 'medium',
            buttons: buttons,
            $content: $('<main/>', {
                role: 'alert',
                text: message,
            }),
            title: _t("Here's your Link !"),
            onForceClose: options && (options.onForceClose || options.confirm_callback),
        }, options)).open({shouldFocusButtons:true});
    };
});
