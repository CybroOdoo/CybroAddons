import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { PosAccessRightPlugin } from "@point_of_sale/app/plugins/access_right_plugin";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

function buildRestrictions(cashier, cache) {
    if (!cashier || !cache) {
        return null;
    }

    const cashierId = cashier.id ? String(cashier.id) : null;
    if (!cashierId) {
        return null;
    }

    let empId = null;
    let userId = null;

    const isEmployeeModel = cashier.model?.modelName === "hr.employee";
    const isUserModel = cashier.model?.modelName === "res.users";

    if (isEmployeeModel) {
        empId = cashierId;
    } else if (isUserModel) {
        userId = cashierId;
    } else if (cache.employees && cashierId in cache.employees) {
        empId = cashierId;
    } else if (cache.users && cashierId in cache.users) {
        userId = cashierId;
    } else {
        userId = cashierId;
    }

    if (empId) {
        if (cashier.user_id) {
            if (typeof cashier.user_id === "number") {
                userId = String(cashier.user_id);
            } else if (Array.isArray(cashier.user_id) && cashier.user_id.length > 0) {
                userId = String(cashier.user_id[0]);
            } else if (typeof cashier.user_id === "object" && cashier.user_id.id) {
                userId = String(cashier.user_id.id);
            }
        }
        if (!userId && cashier.user_id_int) {
            userId = String(cashier.user_id_int);
        }
        if (!userId && cache.emp_to_user_map?.[empId]) {
            userId = cache.emp_to_user_map[empId];
        }
    }

    const userKey = userId;
    const empKey = empId;
    const advancedIds = cache.advanced_ids || [];

    if ((empKey && advancedIds.includes(empKey)) || (userKey && advancedIds.includes(userKey))) {
        return null;
    }

    const userData = userKey ? cache.users?.[userKey] : null;
    const empData = empKey ? cache.employees?.[empKey] : null;

    const checkAllow = (field) => {
        let allowed = true;
        if (userData && field in userData && userData[field] === false) {
            allowed = false;
        }
        if (empData && field in empData && empData[field] === false) {
            allowed = false;
        }
        return allowed;
    };

    return {
        allowNumpad: checkAllow("pos_allow_numpad"),
        allowPayments: checkAllow("pos_allow_payments"),
        allowDiscount: checkAllow("pos_allow_discount"),
        allowQty: checkAllow("pos_allow_qty"),
        allowPriceEdit: checkAllow("pos_allow_price_edit"),
        allowRemoveOrderLine: checkAllow("pos_allow_remove_order_line"),
        allowCustomerSelection: checkAllow("pos_allow_customer_selection"),
        allowPlusMinus: checkAllow("pos_allow_plus_minus"),
    };
}

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.restrictionData = null;
        this.currentRestrictions = null;
        if (this.data) {
            this.data.pos = this;
        }
    },

    async afterProcessServerData() {
        await super.afterProcessServerData(...arguments);
        if (this.data) {
            this.data.pos = this;
        }
        try {
            this.restrictionData = await this.data.call("pos.session", "get_pos_restriction_data", [[]]);
            this.updateRestrictions();
        } catch (error) {
            console.error("Failed to load POS restrictions:", error);
        }
    },

    setCashier(user) {
        const res = super.setCashier(...arguments);
        this.updateRestrictions(user);
        return res;
    },

    updateRestrictions(cashier) {
        const activeCashier = cashier || this.accessRight?.loggedCashier;
        if (!activeCashier || !this.restrictionData) {
            this.currentRestrictions = null;
            return null;
        }
        this.currentRestrictions = buildRestrictions(activeCashier, this.restrictionData);
        return this.currentRestrictions;
    },

    async selectPartner() {
        if (this.currentRestrictions && !this.currentRestrictions.allowCustomerSelection) {
            return false;
        }
        return super.selectPartner(...arguments);
    },
});

patch(PosAccessRightPlugin.prototype, {
    resetCashier() {
        const res = super.resetCashier(...arguments);
        if (this.pos) {
            this.pos.currentRestrictions = null;
        }
        return res;
    },

    get disableClickPayment() {
        if (this.pos?.currentRestrictions && !this.pos.currentRestrictions.allowPayments) {
            return true;
        }
        return super.disableClickPayment;
    },

    get disableValidateOrder() {
        if (this.pos?.currentRestrictions && !this.pos.currentRestrictions.allowPayments) {
            return true;
        }
        return super.disableValidateOrder;
    },

    get disablePartner() {
        if (this.pos?.currentRestrictions && !this.pos.currentRestrictions.allowCustomerSelection) {
            return true;
        }
        return super.disablePartner;
    },

    get disablePriceButton() {
        if (this.pos?.currentRestrictions && !this.pos.currentRestrictions.allowPriceEdit) {
            return true;
        }
        return super.disablePriceButton;
    },

    get disableLinediscount() {
        if (this.pos?.currentRestrictions && !this.pos.currentRestrictions.allowDiscount) {
            return true;
        }
        return super.disableLinediscount;
    },

    get canSwitchSign() {
        if (this.pos?.currentRestrictions && !this.pos.currentRestrictions.allowPlusMinus) {
            return false;
        }
        return super.canSwitchSign;
    },

    get disableBackSpaceButton() {
        if (this.pos?.currentRestrictions && !this.pos.currentRestrictions.allowRemoveOrderLine) {
            return true;
        }
        return super.disableBackSpaceButton;
    },
});

patch(PosOrder.prototype, {
    removeOrderline() {
        const restrictions = this.models?.pos?.currentRestrictions;
        if (restrictions && !restrictions.allowRemoveOrderLine) {
            return false;
        }
        return super.removeOrderline(...arguments);
    },
});

patch(ProductScreen.prototype, {
    getNumpadButtons() {
        const buttons = super.getNumpadButtons(...arguments);
        const restr = this.pos.currentRestrictions;
        if (restr) {
            const digitValues = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", ",", ""];
            return buttons.map((b) => {
                let isDisabled = b.disabled || false;
                const strVal = String(b.value);

                if (!restr.allowNumpad && (digitValues.includes(strVal) || /^[0-9.,]$/.test(strVal))) {
                    isDisabled = true;
                }
                if (!restr.allowQty && strVal === "quantity") {
                    isDisabled = true;
                }
                if (!restr.allowDiscount && strVal === "discount") {
                    isDisabled = true;
                }
                if (!restr.allowPriceEdit && strVal === "price") {
                    isDisabled = true;
                }
                if (!restr.allowPlusMinus && strVal === "-") {
                    isDisabled = true;
                }
                return {
                    ...b,
                    disabled: isDisabled,
                };
            });
        }
        return buttons;
    },

    onNumpadClick(buttonValue) {
        const restr = this.pos.currentRestrictions;
        if (restr) {
            const strVal = String(buttonValue);
            const digitValues = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".", ",", ""];

            if (!restr.allowNumpad && (digitValues.includes(strVal) || /^[0-9.,]$/.test(strVal))) {
                return;
            }
            if (!restr.allowDiscount && strVal === "discount") {
                return;
            }
            if (!restr.allowPriceEdit && strVal === "price") {
                return;
            }
            if (!restr.allowQty && strVal === "quantity") {
                return;
            }
            if (!restr.allowPlusMinus && strVal === "-") {
                return;
            }
            if (!restr.allowRemoveOrderLine && strVal === "Backspace") {
                const order = this.currentOrder;
                const line = order?.getSelectedOrderline();
                if (line && line.getQuantity() === 0) {
                    return;
                }
            }
        }
        return super.onNumpadClick(...arguments);
    },

    async addProductToOrder(product) {
        const restr = this.pos.currentRestrictions;
        if (restr && !restr.allowQty) {
            const order = this.pos.getOrder();
            if (order) {
                const resolvedTemplateId = typeof product === "number" ? product : product?.id;
                const existingLine = order.lines?.find((line) => {
                    const lineTemplateId = line.product_id?.product_tmpl_id?.id
                        || line.product_id?.product_tmpl_id
                        || line.product_tmpl_id?.id
                        || line.product_tmpl_id;
                    return lineTemplateId === resolvedTemplateId || line.product_id?.id === resolvedTemplateId;
                });
                if (existingLine) {
                    return;
                }
            }
        }
        return super.addProductToOrder(...arguments);
    },

    async onClickPay() {
        const restr = this.pos.currentRestrictions;
        if (restr && !restr.allowPayments) {
            return;
        }
        return super.onClickPay(...arguments);
    },
});

patch(PaymentScreen.prototype, {
    async validateOrder() {
        const restr = this.pos.currentRestrictions;
        if (restr && !restr.allowPayments) {
            return;
        }
        return super.validateOrder(...arguments);
    },
});