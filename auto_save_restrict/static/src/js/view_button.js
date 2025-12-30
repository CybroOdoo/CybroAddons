/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ViewButton } from "@web/views/view_button/view_button";
import { SettingsConfirmationDialog } from "@web/webclient/settings_form_view/settings_confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { pick } from "@web/core/utils/objects";

patch(ViewButton.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialogService = useService("dialog");
        this.actionService = useService("action");
    },

    async onClick(ev) {
        const model = this.props.record || this.props.model;
        const hasUnsavedChanges =
            model && typeof model.isDirty === "function" && (await model.isDirty());

        if (hasUnsavedChanges) {
            if (this.props.tag === "a") {
                ev.preventDefault();
            }
            ev.stopPropagation();

            const proceed = await this._confirmSave(model);
            if (!proceed) {
                return;
            }
            if (this.props.clickParams) {
                return this.env.onClickViewButton({
                    clickParams: this.props.clickParams,
                    getResParams: () =>
                        pick(model, "context", "evalContext", "resModel", "resId", "resIds"),
                });
            }
            return;
        }

        // Normal button behavior (no unsaved changes)
        if (this.props.tag === "a") {
            ev.preventDefault();
        }
        if (this.props.onClick) {
            return this.props.onClick();
        }
        if (this.props.clickParams) {
            return this.env.onClickViewButton({
                clickParams: this.props.clickParams,
                getResParams: () =>
                    pick(model, "context", "evalContext", "resModel", "resId", "resIds"),
            });
        }
    },

    async _confirmSave(model) {
        let proceed = true;

        await new Promise((resolve) => {
            this.dialogService.add(SettingsConfirmationDialog, {
                body: _t("Would you like to save your changes?"),
                confirm: async () => {
                    try {
                        await model.save();
                        proceed = true;
                    } catch (e) {
                        console.error("Save failed:", e);
                        proceed = false;
                    }
                    resolve();
                },
                cancel: async () => {
                    if (model?.discard) await model.discard();
                    proceed = true;
                    resolve();
                },
                stayHere: () => {
                    proceed = false;
                    resolve();
                },
            });
        });

        return proceed;
    },
});