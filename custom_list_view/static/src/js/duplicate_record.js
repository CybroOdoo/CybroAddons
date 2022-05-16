odoo.define('custom_list_view.ListController', function (require) {
"use strict";

var core = require('web.core');
var ListController = require('web.ListController');
var DataExport = require('web.DataExport');
var Dialog = require('web.Dialog');
var ListConfirmDialog = require('web.ListConfirmDialog');
var session = require('web.session');
const viewUtils = require('web.viewUtils');
var _t = core._t;
var qweb = core.qweb;

var duplicate={

    init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.hasActionMenus = params.hasActionMenus;
        },
        willStart() {
        const sup = this._super(...arguments);
        const acl = session.user_has_group('base.group_allow_export').then(hasGroup => {
            this.isExportEnable = hasGroup;
        });
        return Promise.all([sup, acl]);
    },
    _onDuplicateRecord: function () {
            var self = this;
            var def = [];
            var ids = this.selectedRecords
            _.each(ids, function (id) {
                def.push(self.model.duplicateRecord(id));
            });
            return $.when.apply($, def).done(function () {
                self.reload();
            });
        },
    _discardChanges: function (recordID) {
        if ((recordID || this.handle) === this.handle) {
            recordID = this.renderer.getEditableRecordID();
            if (recordID === null) {
                return Promise.resolve();
            }
        }
        var self = this;
        return this._super(recordID).then(function () {
            self.updateButtons('readonly');
        });
    },
   _domainToResIds: function (domain, limit) {
        return this._rpc({
            model: this.modelName,
            method: 'search',
            args: [domain],
            kwargs: {
                limit: limit,
            },
        });
    },
    _getExportDialogWidget() {
        let state = this.model.get(this.handle);
        let defaultExportFields = this.renderer.columns.filter(field => field.tag === 'field').map(field => field.attrs.name);
        let groupedBy = this.renderer.state.groupedBy;
        const domain = this.isDomainSelected && state.getDomain();
        return new DataExport(this, state, defaultExportFields, groupedBy,
            domain, this.getSelectedIds());
    },
   _getPagingInfo: function (state) {
        if (!state.count) {
            return null;
        }
        return this._super(...arguments);
    },
   _getActionMenuItems: function (state) {
        if (!this.hasActionMenus || !this.selectedRecords.length) {
            return null;
        }
        const props = this._super(...arguments);
        const otherActionItems = [];
        if (this.isExportEnable) {
            otherActionItems.push({
                description: _t("Export"),
                callback: () => this._onExportData()
            });
        }
        if (this.archiveEnabled) {
            otherActionItems.push({
                description: _t("Archive"),
                callback: () => {
                    Dialog.confirm(this, _t("Are you sure that you want to archive all the selected records?"), {
                        confirm_callback: () => this._toggleArchiveState(true),
                    });
                }
            }, {
                description: _t("Unarchive"),
                callback: () => this._toggleArchiveState(false)
            });
        }
        if (this.activeActions.delete) {
            otherActionItems.push({
                description: _t("Delete"),
                callback: () => this._onDeleteSelectedRecords()
            });
        }
         if (this.activeActions.delete) {
            otherActionItems.push({
                description: _t("Duplicate"),
                callback: () => this._onDuplicateSelectedRecords()
            });
        }

        return Object.assign(props, {
            items: Object.assign({}, this.toolbarActions, { other: otherActionItems }),
            context: state.getContext(),
            domain: state.getDomain(),
            isDomainSelected: this.isDomainSelected,
        });
    },
   _onDuplicateSelectedRecords: async function () {

            this._onDuplicateRecord();

    },
    };
ListController.include(duplicate)
});
