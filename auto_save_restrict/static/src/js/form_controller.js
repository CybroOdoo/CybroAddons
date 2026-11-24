import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SettingsConfirmationDialog } from "@web/webclient/settings_form_view/settings_confirmation_dialog";

patch(FormController.prototype, {
    /** Patch FormController to restrict auto-saving in form views. */

    async beforeLeave({ forceLeave } = {}) {
        if (forceLeave) {
            return true;
        }
        const isDirty = await this.model.root.isDirty();
        if (isDirty) {
            return this._confirmSave();
        }
        return super.beforeLeave(...arguments);
    },

    async beforeVisibilityChange() {
        // Prevent background auto-saving when switching browser tabs.
        return;
    },

    async beforeExecuteActionButton(clickParams) {
        if (clickParams.special === "cancel") {
            if (this.props.onDiscard) {
                this.props.onDiscard(this.model.root);
            }
            return;
        }
        if (clickParams.special === "save") {
            return super.beforeExecuteActionButton(...arguments);
        }
        const isDirty = await this.model.root.isDirty();
        if (isDirty) {
            const proceed = await this._confirmSave();
            if (!proceed) {
                return false;
            }
        }
        return super.beforeExecuteActionButton(...arguments);
    },

    async create() {
        const isDirty = await this.model.root.isDirty();
        if (isDirty) {
            const proceed = await this._confirmSave();
            if (!proceed) {
                return;
            }
        }
        return super.create(...arguments);
    },

    async _confirmSave() {
        let _continue = true;
        const dialog = this.dialogService || this.env.services.dialog;
        await new Promise((resolve) => {
            dialog.add(SettingsConfirmationDialog, {
                body: _t("Would you like to save your changes?"),
                confirm: async () => {
                    const saved = await this.save();
                    _continue = Boolean(saved);
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
});
