import { test, expect, describe } from "@odoo/hoot";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { mountWithCleanup } from "@web/../tests/web_test_helpers";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { SelectPartnerButton } from "@point_of_sale/app/screens/product_screen/control_buttons/select_partner_button/select_partner_button";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";

definePosModels();

describe("pos_access_right_hr", () => {
    test("getCashier returns cashier when set", async () => {
        const store = await setupPosEnv();
        const emp = store.models["hr.employee"].get(2);
        store.setCashier(emp);
        expect(store.getCashier()).toBe(emp);
    });

    test("ActionpadWidget payment disabled check", async () => {
        const store = await setupPosEnv();
        const emp = store.models["hr.employee"].get(2);
        emp.disable_payment = true;
        store.setCashier(emp);

        expect(ActionpadWidget.prototype.isPaymentDisabled.call({ pos: store })).toBe(true);

        emp.disable_payment = false;
        expect(ActionpadWidget.prototype.isPaymentDisabled.call({ pos: store })).toBe(false);
    });

    test("SelectPartnerButton customer selection disabled check", async () => {
        const store = await setupPosEnv();
        const emp = store.models["hr.employee"].get(2);
        emp.disable_customer = true;
        store.setCashier(emp);

        expect(SelectPartnerButton.prototype.isCustomerSelectionDisabled.call({ pos: store })).toBe(true);

        emp.disable_customer = false;
        expect(SelectPartnerButton.prototype.isCustomerSelectionDisabled.call({ pos: store })).toBe(false);
    });

    test("pos store pay is blocked when cashier has disable_payment", async () => {
        const store = await setupPosEnv();
        const emp = store.models["hr.employee"].get(2);
        emp.disable_payment = true;
        store.setCashier(emp);

        let dialogShown = false;
        store.dialog = {
            add: () => {
                dialogShown = true;
            },
        };

        await store.pay();
        expect(dialogShown).toBe(true);
    });

    test("ProductScreen getNumpadButtons respects cashier restrictions", async () => {
        const store = await setupPosEnv();
        store.addNewOrder();
        const order = store.getOrder();
        const productScreen = await mountWithCleanup(ProductScreen, {
            props: { orderUuid: order.uuid },
        });

        const emp = store.models["hr.employee"].get(2);
        emp.disable_qty = true;
        emp.disable_discount = true;
        emp.disable_price = true;
        emp.disable_numpad = true;
        emp.disable_plus_minus = true;
        emp.disable_remove_button = true;
        store.setCashier(emp);

        const buttons = productScreen.getNumpadButtons();
        const qtyBtn = buttons.find((b) => b.value === "quantity");
        const discBtn = buttons.find((b) => b.value === "discount");
        const priceBtn = buttons.find((b) => b.value === "price");
        const oneBtn = buttons.find((b) => b.value === "1");
        const minusBtn = buttons.find((b) => b.value === "-");
        const backspaceBtn = buttons.find((b) => b.value === "Backspace");

        expect(qtyBtn.disabled).toBe(true);
        expect(discBtn.disabled).toBe(true);
        expect(priceBtn.disabled).toBe(true);
        expect(oneBtn.disabled).toBe(true);
        expect(minusBtn.disabled).toBe(true);
        expect(backspaceBtn.disabled).toBe(true);

        emp.disable_numpad = false;
        emp.disable_qty = false;
        emp.disable_discount = false;
        emp.disable_price = false;
        emp.disable_plus_minus = false;
        emp.disable_remove_button = false;
        const unconstrainedButtons = productScreen.getNumpadButtons();
        expect(unconstrainedButtons.find((b) => b.value === "quantity").disabled).toBe(false);
        expect(unconstrainedButtons.find((b) => b.value === "1").disabled).toBe(false);
    });
});
