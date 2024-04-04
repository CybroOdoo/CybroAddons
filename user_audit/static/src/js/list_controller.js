/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ListController } from '@web/views/list/list_controller';
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import {
    deleteConfirmationMessage,
    ConfirmationDialog,
} from "@web/core/confirmation_dialog/confirmation_dialog";

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },
    // For tracking Create operation
    async createRecord({group} = {}) {
        const list = (group && group.list) || this.model.root;
        var resModel = this.model.root.resModel;
        if (this.editable && !list.isGrouped) {
            if (!(list instanceof DynamicRecordList)) {
                throw new Error("List should be a DynamicRecordList");
            }
            await list.leaveEditMode();
            if (!list.editedRecord) {
                await (group || list).addNewRecord(this.editable === "top");
            }
            this.render();
        } else {
            this.orm.call(
                "user.audit",
                "create_audit_log_for_create",
                [resModel],
            ).then(function(data) {})
            await this.props.createRecord();
        }
    },
    //for tracking Read operation
    async openRecord(record) {
        if (this.archInfo.openAction) {
            this.actionService.doActionButton({
                name: this.archInfo.openAction.action,
                type: this.archInfo.openAction.type,
                resModel: record.resModel,
                resId: record.resId,
                resIds: record.resIds,
                context: record.context,
                onClose: async () => {
                    await record.model.root.load();
                    record.model.notify();
                },
            });
        } else {
            const activeIds = this.model.root.records.map((datapoint) => datapoint.resId);
            this.props.selectRecord(record.resId, {
                activeIds
            });
        }
        var resModel = record.resModel;
        var resId = record.resId
        this.orm.call(
            "user.audit",
            "create_audit_log_for_read",
            [resModel, resId],
        ).then(function(data) {})
    },
    //Multiple Record Delete Confirmation Popup
    get deleteConfirmationDialogProps() {
        const root = this.model.root;
        let body = deleteConfirmationMessage;
        if (root.isDomainSelected || root.selection.length > 1) {
            body = _t("Are you sure you want to delete these records?");
        }
        return {
            title: _t("Bye-bye, record!"),
            body,
            confirmLabel: _t("Delete"),
            confirm: async () => {
                await this.model.root.deleteRecords();
                const root = this.model.root;
                var resId = root.records[0].resId
                var resModel = this.model.root.resModel;
                this.orm.call(
                    "user.audit",
                    "create_audit_log_for_delete",
                    [resModel, resId],
                ).then(function(data) {
                })
            },
            cancel: () => {},
            cancelLabel: _t("No, keep it"),
        };
    },
    //For managing Delete of multiple records
    async onDeleteSelectedRecords() {
        this.dialogService.add(ConfirmationDialog, this.deleteConfirmationDialogProps);
    }
})
