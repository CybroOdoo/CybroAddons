import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SettingsConfirmationDialog } from "@web/webclient/settings_form_view/settings_confirmation_dialog";

patch(ListController.prototype, {
    /** Patch ListController to restrict auto-saving in list views. */

    async beforeLeave(ev) {
        if (this.model.root.editedRecord) {
            let _continue = true;
            const dialog = this.dialogService || this.env.services.dialog;
            await new Promise((resolve) => {
                dialog.add(SettingsConfirmationDialog, {
                    body: _t("Would you like to save your changes?"),
                    confirm: async () => {
                        await this.onClickSave();
                        _continue = true;
                        resolve();
                    },
                    cancel: async () => {
                        await this.onClickDiscard();
                        _continue = true;
                        resolve();
                    },
                    stayHere: () => {
                        _continue = false;
                        resolve();
                    },
                });
            });
            return _continue;
        }
        return super.beforeLeave(...arguments);
    },
});
