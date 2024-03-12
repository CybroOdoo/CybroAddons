/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ConfirmationDialog.prototype, {
    setup() {
        super.setup();
        this.action = useService("action");
        },
        _open_form_view(ev) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'res.partner.category',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'current',
            res_id: this.props.recordResId,
            context: {
                'dialog_size': 'medium',
            },
        });
    return this.props.close();
    },
        });
ConfirmationDialog.props = {
    ...ConfirmationDialog.props,
    open_form_viewClass: { type: String, optional: true },
    open_form_view: { type: Function, optional: true },
    open_form_viewLabel: { type: String, optional: true },
    recordResId: {type: Number, optional: true}
};
ConfirmationDialog.defaultProps = {
...ConfirmationDialog.defaultProps,
    open_form_viewLabel: _t("Open Form View"),
    open_form_viewClass: "btn-primary",
};
