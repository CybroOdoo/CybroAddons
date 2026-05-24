/** @odoo-module */

/**
 * Extends ConfirmationDialog to add option
 * to open form view of many2many record.
 */

import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ConfirmationDialog.prototype, {
    setup() {
        /**
         * Initializes the component and loads required services.
         *
         * Services:
         * - action: Used to trigger backend actions such as opening form views.
         */
        super.setup();
        this.action = useService("action");
    },
    openFormView(ev) {
        /**
         * Opens the form view of the selected record.
         *
         * Uses the action service to trigger a window action
         * based on the provided model and record ID.
         */
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: this.props.resModel,
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current',
            res_id: this.props.resId,
            context: {
                'dialog_size': 'medium',
            },
        });
    return this.props.close();
    },
});

ConfirmationDialog.props = {
    ...ConfirmationDialog.props,
    openFormView: { type: Function, optional: true },
    openFormViewLabel: { type: String, optional: true },
    resModel: { type: String, optional: true },
    resId: {type: Number, optional: true}
};

ConfirmationDialog.defaultProps = {
...ConfirmationDialog.defaultProps,
    openFormViewLabel: _t("Open Form View"),
};
