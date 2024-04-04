/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import {
    deleteConfirmationMessage,
    ConfirmationDialog,
} from "@web/core/confirmation_dialog/confirmation_dialog";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },
    //For managing Save button click
    async saveButtonClicked(params = {}) {
        super.saveButtonClicked(params);
        var resModel = this.model.root.resModel;
        var resId = this.model.root.resId;
        this.orm.call(
            "user.audit",
            "create_audit_log_for_write",
            [resModel, resId],
        ).then(function(data) {})
    },
    //For managing Create operation
    async create() {
        super.create();
        var resModel = this.model.root.resModel;
        this.orm.call(
            "user.audit",
            "create_audit_log_for_create",
            [resModel],
        ).then(function(data) {})
    },
    //Record Delete Confirmation Popup
    get deleteConfirmationDialogProps() {
        return {
            title: _t("Bye-bye, record!"),
            body: deleteConfirmationMessage,
            confirm: async () => {
                await this.model.root.delete();
                this.orm.call(
                    "user.audit",
                    "create_audit_log_for_delete",
                    [this.model.root.resModel, this.model.root.resId],
                ).then(function(data) {})
                if (!this.model.root.resId) {
                    this.env.config.historyBack();
                }
            },
            confirmLabel: _t("Delete"),
            cancel: () => {},
            cancelLabel: _t("No, keep it"),
        };
    },
    //For managing Delete operation
    async deleteRecord() {
        this.dialogService.add(ConfirmationDialog, this.deleteConfirmationDialogProps);
    }
})
