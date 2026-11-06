import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PosStore.prototype, {
    setCashier(cashier) {
        this.cashier = cashier;
        return super.setCashier(...arguments);
    },

    getCashier() {
        if (this.cashier) {
            return this.cashier;
        }
        const order = this.getOrder ? this.getOrder() : null;
        if (order && order.employee_id) {
            return order.employee_id;
        }
        if (this.config && this.config.id) {
            const cashierId = Number(
                sessionStorage.getItem(`connected_cashier_${this.config.id}`)
            );
            if (cashierId && this.models) {
                const employees = this.models["hr.employee"];
                const employee = employees && employees.get ? employees.get(cashierId) : null;
                if (employee) {
                    return employee;
                }
                const users = this.models["res.users"];
                const user = users && users.get ? users.get(cashierId) : null;
                if (user) {
                    return user;
                }
            }
        }
        return this.user;
    },

    async pay() {
        const cashier = this.getCashier();
        if (cashier && cashier.disable_payment) {
            this.dialog.add(AlertDialog, {
                title: _t("Access Denied"),
                body: _t("You are not allowed to make payments."),
            });
            return;
        }
        await super.pay(...arguments);
    },
});
