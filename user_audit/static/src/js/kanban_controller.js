import { patch } from "@web/core/utils/patch";
import { KanbanController } from '@web/views/kanban/kanban_controller';
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import {
    deleteConfirmationMessage,
    ConfirmationDialog,
} from "@web/core/confirmation_dialog/confirmation_dialog";
import { DynamicList } from "@web/model/relational_model/dynamic_list";


patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },

    CustomDeleteConfirmationDialogProps(record) {
        return {
            confirm: async () => {
                const isDynamicList = this.model.root instanceof DynamicList;
                const resModel = this.model.root.resModel;
                const resId = record.resId;
                if (isDynamicList) {
                    await this.model.root.deleteRecords([record]);
                } else {
                    record.forEach((r) => r.delete());
                }
                await this.orm.call(
                    "user.audit",
                    "create_audit_log",
                    [resModel, [resId], 'delete'],
                ).catch(() => {});
            }
        };
    },

    deleteRecord(record) {
        this.deleteRecordsWithConfirmation(this.CustomDeleteConfirmationDialogProps(record), [record]);
    },

    //for tracking Read operation
    async openRecord(record, { newWindow } = {}) {
        const resModel = record.resModel;
        const resId = record.resId;
        await this.orm.call(
            "user.audit",
            "create_audit_log",
            [resModel, resId,'read'],
        ).catch(() => {});
        const activeIds = this.model.root.records.map((datapoint) => datapoint.resId);
        this.props.selectRecord(record.resId, { activeIds, newWindow });
    },

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
                const records = this.model.root.selection.map((record) => record.resId);
                const resModel = this.model.root.resModel;
                await this.model.root.deleteRecords();
                await this.orm.call(
                    "user.audit",
                    "create_audit_log",
                    [resModel, records,'delete'],
                ).catch(() => {});
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
