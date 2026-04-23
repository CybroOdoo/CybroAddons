/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { KanbanController } from '@web/views/kanban/kanban_controller';
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { DynamicRecordList } from "@web/model/relational_model/dynamic_record_list";
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

    // For tracking Delete operation
    CustomDeleteConfirmationDialogProps(record) {

            return {
                confirm: async () => {
                    const resId = this.model.root.resId
                    const isDynamicList = this.model.root instanceof DynamicList;
                    await this.orm.call(
                        "user.audit",
                        "create_audit_log",
                        [this.model.root.resModel, [record.resId],'delete'],)
                    if (isDynamicList) {
                        await this.model.root.deleteRecords([record]);
                    } else {
                        record.forEach((r) => r.delete());
                    }
                }
            }
    },

    deleteRecord(record) {
        this.deleteRecordsWithConfirmation(this.CustomDeleteConfirmationDialogProps(record), [record]);
    },
    // For tracking Create operation
    async createRecord() {
        const { onCreate } = this.props.archInfo;
        const { root } = this.model;
        if (this.canQuickCreate && onCreate === "quick_create") {
            const firstGroup = root.groups.find((group) => !group.isFolded) || root.groups[0];
            if (firstGroup.isFolded) {
                await firstGroup.toggle();
            }
            this.quickCreateState.groupId = firstGroup.id;
        } else if (onCreate && onCreate !== "quick_create") {
            const options = {
                additionalContext: root.context,
                onClose: async ({ noReload } = {}) => {
                    if (!noReload) {
                        await root.load();
                        this.model.useSampleModel = false;
                        this.render(true); // FIXME WOWL reactivity
                    }
                },
            };
            await this.actionService.doAction(onCreate, options);
        } else {
            await this.props.createRecord();
        }
        var resModel = this.model.root.resModel;
            let resId = this.model.root.resId
            await this.orm.call(
            "user.audit",
            "create_audit_log",
            [resModel,resId,'create'],
        )
    },

    //for tracking Read operation
    async openRecord(record, { newWindow } = {}) {
        const activeIds = this.model.root.records.map((datapoint) => datapoint.resId);
        this.props.selectRecord(record.resId, { activeIds, newWindow });
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
