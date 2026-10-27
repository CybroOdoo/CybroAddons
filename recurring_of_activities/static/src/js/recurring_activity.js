/** @odoo-module **/
import { ActivityMenu } from "@mail/core/web/activity_menu";
import { ReferenceField } from "@web/views/fields/reference/reference_field";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

// Patching and added the manage recurring button
patch(ActivityMenu.prototype, {
    onClickCustomLink() {
        this.dropdown?.close();
        const actionService = this.action || this.env.services.action;
        actionService.doAction(
            {
                name: "Recurring Activities",
                type: "ir.actions.act_window",
                res_model: "recurring.activity",
                views: [[false, "list"], [false, "form"]],
                target: "current",
                context: { create: true },
            },
            {
                clearBreadcrumbs: true,
            }
        );
    },
});

// Patch ReferenceField to validate that the selected model is installed before attempting to load records
patch(ReferenceField.prototype, {
    async updateModel(value) {
        if (value && (this.props.record?.resModel === "recurring.activity" || this.props.name === "action")) {
            let isInstalled = true;
            try {
                if (this.env.services.orm) {
                    isInstalled = await this.env.services.orm.silent.call(
                        "recurring.activity",
                        "check_model_installed",
                        [value]
                    );
                }
            } catch {
                try {
                    const count = await this.env.services.orm.silent.searchCount("ir.model", [["model", "=", value]]);
                    isInstalled = count > 0;
                } catch {
                    isInstalled = false;
                }
            }

            if (!isInstalled) {
                this.state.currentRelation = false;
                await this.props.record.update({ [this.props.name]: false });

                const message = _t("The module is not installed, so we can't configure any records for this.");
                if (this.env.services.dialog) {
                    this.env.services.dialog.add(ConfirmationDialog, {
                        title: _t("Validation Error"),
                        body: message,
                        confirmLabel: _t("Ok"),
                        confirmClass: "btn-primary",
                        cancel: false,
                    });
                } else if (this.env.services.notification) {
                    this.env.services.notification.add(message, {
                        type: "warning",
                        title: _t("Validation Error"),
                    });
                }
                return;
            }
        }
        return super.updateModel(...arguments);
    },
});
