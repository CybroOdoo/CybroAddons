/** @odoo-module **/

import { AccountMoveKanbanController } from "@account/views/account_move_kanban/account_move_kanban_controller";
import { AccountMoveListController } from "@account/views/account_move_list/account_move_list_controller";
import { onWillStart, proxy } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

export function digitizeBillControllerPatch() {
    return {
        setup() {
            super.setup(...arguments);
            this.actionService = useService("action");
            this.orm = useService("orm");
            this.onClickDigitize = this.onClickDigitize.bind(this);
            if (this.state) {
                this.state.button_state = false;
            } else {
                this.state = proxy({
                    button_state: false,
                });
            }

            onWillStart(async () => {
                const hasInvoiceAccess = await user.hasGroup("account.group_account_invoice");
                if (!hasInvoiceAccess) {
                    this.state.button_state = false;
                    return;
                }
                const digitizeBillParam = await this.orm.silent.call(
                    "digitize.bill",
                    "is_digitize_bill_enabled",
                    []
                );
                this.state.button_state = Boolean(digitizeBillParam);
            });
        },

        onClickDigitize() {
            this.actionService.doAction({
                name: _t("Upload Bill"),
                type: "ir.actions.act_window",
                res_model: "digitize.bill",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
            });
        },
    };
}

patch(AccountMoveListController.prototype, digitizeBillControllerPatch());
patch(AccountMoveKanbanController.prototype, digitizeBillControllerPatch());
