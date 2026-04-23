/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ListController } from '@web/views/list/list_controller';
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { DynamicRecordList } from "@web/model/relational_model/dynamic_record_list";
import {
    deleteConfirmationMessage,
    ConfirmationDialog,
} from "@web/core/confirmation_dialog/confirmation_dialog";
import { DynamicList } from "@web/model/relational_model/dynamic_list";


patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },
    // For tracking Create operation
    async createRecord({group} = {}) {
        if (!this.model.isReady && !this.model.config.groupBy.length && this.editable) {
            // If the view isn't grouped and the list is editable, a new record row will be added,
            // in edition. In this situation, we must wait for the model to be ready.
            await this.model.whenReady;
        }
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
            this.props.createRecord().then(async() =>{
                if (this.__owl__.status !== 3) {
                    await this.orm.call(
                        "user.audit",
                        "create_audit_log",
                        [resModel,false,'create'],
                    )
                }
            })

        }
    },
    //for tracking Read operation
    async openRecord(record, { force, newWindow } = { force: false }) {
        const dirty = await record.isDirty();
        if (dirty) {
            await record.save();
        }
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
        var resModel = record.resModel;
        var resId = record.resId
        await this.orm.call(
            "user.audit",
            "create_audit_log",
            [resModel, resId,'read'],
        )
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
                const resId = this.model.root.records[0].resId
                const records = this.model.root.selection.map((record) => record.resId);
                await this.model.root.deleteRecords();
                const root = this.model.root;

                var resModel = this.model.root.resModel;
                this.orm.call(
                    "user.audit",
                    "create_audit_log",
                    [resModel, records,'delete'],
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
