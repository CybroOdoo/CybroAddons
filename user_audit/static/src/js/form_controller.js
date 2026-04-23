/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import {
    deleteConfirmationMessage,
    ConfirmationDialog,
} from "@web/core/confirmation_dialog/confirmation_dialog";
import { executeButtonCallback, useViewButtons } from "@web/views/view_button/view_button_hook";


patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },
    //For managing Save button click for getting write data
    async saveButtonClicked(params = {}) {
        super.saveButtonClicked(params);
        var resModel = this.model.root.resModel;
        var resId = this.model.root.resId;
        await this.orm.call(
            "user.audit",
            "create_audit_log",
            [resModel, resId,'write'],
        )
    },
    //For managing Create operation
    async create() {
        const dirty = await this.model.root.isDirty();
        const onError = (error, options) => this.onSaveError(error, options, true);
        const canProceed = !dirty || (await this.model.root.save({ onError }));
        if (canProceed) {
            await executeButtonCallback(this.ui.activeElement, () =>
                this.model.load({ resId: false })
            );
            var resModel = this.model.root.resModel;
            let resId = this.model.root.resId
            await this.orm.call(
            "user.audit",
            "create_audit_log",
            [resModel,resId,'create'],
        )
        }
    },

    //Record Delete Confirmation Popup
    get deleteConfirmationDialogProps() {
        return {
            confirm: async () => {
                const resId = this.model.root.resId
                this.orm.call(
                    "user.audit",
                    "create_audit_log",
                    [this.model.root.resModel, [resId],'delete'],
                ).then(async()=> await this.model.root.delete())

                if (!this.model.root.resId) {
                    this.env.config.historyBack();
                }
            },
        };
    },
    //For managing Delete operation
    async deleteRecord() {
        this.deleteRecordsWithConfirmation(this.deleteConfirmationDialogProps, [this.model.root]);
    }
})
