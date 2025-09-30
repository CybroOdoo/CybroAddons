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
        this.actionService = useService("action");   // use this instead of old DOM
    },

    async onClick(ev) {
        const model = this.props.record || this.props.model;
        const hasUnsavedChanges =
            model && typeof model.isDirty === "function" && (await model.isDirty());

        if (hasUnsavedChanges) {
            const proceed = await this._confirmSave(model);
            if (!proceed) return;
        }

        // Normal button behavior
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
                        //  use Action Service instead of onClickViewButton (avoids `el=null`)
                        if (this.props.clickParams) {
                            this.actionService.doActionButton({
                                name: this.props.clickParams.name,
                                type: "object",
                                resModel: model.resModel,
                                resId: model.resId,
                                context: model.context,
                            });
                        }
                    } catch (e) {
                        console.error("Save failed:", e);
                    }
                    resolve();
                },
                cancel: async () => {
                    if (model?.discard) await model.discard();
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
