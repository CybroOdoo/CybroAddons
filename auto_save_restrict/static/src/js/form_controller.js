/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SettingsConfirmationDialog } from "@web/webclient/settings_form_view/settings_confirmation_dialog";

// Save original method reference
const _superOnPagerUpdate = FormController.prototype.onPagerUpdate;

patch(FormController.prototype, {
    async beforeLeave() {
        const dirty = await this.model.root.isDirty();
        if (dirty) {
            return this._confirmSave();
        }
        return true;
    },

    beforeUnload() {},

    async _confirmSave() {
        let _continue = true;
        await new Promise((resolve) => {
            this.dialogService.add(SettingsConfirmationDialog, {
                body: _t("Would you like to save your changes?"),
                confirm: async () => {
                    await this.save();
                    _continue = true;
                    resolve();
                },
                cancel: async () => {
                    await this.model.root.discard();
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
    },

    async onPagerUpdate(value) {
        const proceed = await this.beforeLeave();
        if (!proceed) {
            return;
        }
        await this.model.root.discard();
        return _superOnPagerUpdate.call(this, value);
    },
});
