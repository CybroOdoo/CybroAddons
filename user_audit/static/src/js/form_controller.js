import { onMounted } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";


patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        // Track read when opening record directly (e.g. by URL or navigation)
        onMounted(async () => {
            const record = this.model.root;
            if (record && record.resId && !record.isNew) {
                await this.orm.call(
                    "user.audit",
                    "create_audit_log",
                    [record.resModel, record.resId, 'read'],
                ).catch(() => {});
            }
        });
    },

    // For managing Save button click for getting write/create data
    async saveButtonClicked(params = {}) {
        const record = this.model.root;
        const isNew = record.isNew;
        const resModel = record.resModel;
        const saved = await super.saveButtonClicked(params);
        const resId = record.resId;
        if (saved && resId) {
            const operationType = isNew ? 'create' : 'write';
            await this.orm.call(
                "user.audit",
                "create_audit_log",
                [resModel, resId, operationType],
            ).catch(() => {});
        }
    },

    // Record Delete Confirmation Popup
    get deleteConfirmationDialogProps() {
        return {
            confirm: async () => {
                const record = this.model.root;
                const resId = record.resId;
                const resModel = record.resModel;
                await record.delete();
                if (!record.resId) {
                    await this.orm.call(
                        "user.audit",
                        "create_audit_log",
                        [resModel, [resId], 'delete'],
                    ).catch(() => {});
                    this.env.config.historyBack();
                }
            },
        };
    },

    // For managing Delete operation
    async deleteRecord() {
        this.deleteRecordsWithConfirmation(this.deleteConfirmationDialogProps, [this.model.root]);
    }
})
