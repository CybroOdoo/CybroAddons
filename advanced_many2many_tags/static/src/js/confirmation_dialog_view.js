/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog, confirmationDialogProps } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { t } from "@odoo/owl";

/**
 * Extends the ConfirmationDialog to provide an option to open
 * the related record in its form view.
 */
patch(ConfirmationDialog.prototype, {
    setup() {
        super.setup();
        this.action = useService("action");
    },
    openFormView() {
        if (this.props.resModel && this.props.recordResId) {
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: this.props.resModel,
                view_mode: "form",
                views: [[false, "form"]],
                target: "current",
                res_id: this.props.recordResId,
            });
        }
        if (typeof this.props.close === "function") {
            this.props.close();
        }
    },
});

Object.assign(confirmationDialogProps, {
    openFormViewClass: t.string().optional("btn-primary"),
    openFormViewLabel: t.string().optional(_t("Open Form View")),
    resModel: t.string().optional(),
    recordResId: t.number().optional(),
});


