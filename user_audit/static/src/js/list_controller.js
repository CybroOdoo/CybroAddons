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

    //for tracking Read operation
    async openRecord(record, { force, newWindow } = { force: false }) {
        const dirty = await record.isDirty();
        if (dirty) {
            await record.save();
        }
        const resModel = record.resModel;
        const resId = record.resId;
        await this.orm.call(
            "user.audit",
            "create_audit_log",
            [resModel, resId,'read'],
        ).catch(() => {});
        if (this.props.allowOpenAction && this.archInfo.openAction) {
            this.actionService.doActionButton(
                {
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
                },
                {
                    newWindow,
                }
            );
        } else {
            const activeIds = this.model.root.records.map((datapoint) => datapoint.resId);
            this.props.selectRecord(record.resId, { activeIds, force, newWindow });
        }
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
