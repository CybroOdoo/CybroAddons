/** @odoo-module */

import { expect, test } from "@odoo/hoot";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { translatedTerms, translationLoaded } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import "@pos_restrict_product_stock/js/OrderScreen";

function makeLine(displayName, { isRestrictProduct, qtyAvailable, virtualAvailable, type = "consu", toWeight = false }) {
    return {
        config: { is_restrict_product: isRestrictProduct },
        product_id: {
            display_name: displayName,
            qty_available: qtyAvailable,
            virtual_available: virtualAvailable,
            type,
            to_weight: toWeight,
        },
    };
}

function makeContext(stockType, lines) {
    const dialogCalls = [];
    return {
        context: {
            config: { stock_type: stockType },
            getOrder: () => ({ getOrderlines: () => lines }),
            dialog: {
                add: (component, props) => dialogCalls.push({ component, props }),
            },
        },
        dialogCalls,
    };
}

/**
 * _t() returns a lazy, not-yet-translated string until the translation
 * bundle is marked loaded; reading its value before that throws
 * "translation error". A full POS session sets this during boot, but
 * these bare unit tests never do, so we flip the flag ourselves for the
 * duration of the call and restore it after (translatedTerms is shared
 * globally across every module's tests on this page).
 */
async function withTranslationsLoaded(callback) {
    const original = translatedTerms[translationLoaded];
    translatedTerms[translationLoaded] = true;
    try {
        return await callback();
    } finally {
        translatedTerms[translationLoaded] = original;
    }
}

/**
 * The "no out-of-stock lines" branch calls `return super.pay()`, which
 * needs the real PosStore's component/service internals we don't stub
 * here. We only care whether the out-of-stock dialog was skipped.
 */
async function callIgnoringSuperErrors(context) {
    try {
        return await PosStore.prototype.pay.call(context);
    } catch {
        return undefined;
    }
}

test("warns before paying when a line is out of stock (qty_on_hand mode)", async () => {
    const lines = [
        makeLine("Test Product", {
            isRestrictProduct: true,
            qtyAvailable: 0,
            virtualAvailable: 100,
        }),
    ];
    const { context, dialogCalls } = makeContext("qty_on_hand", lines);

    await withTranslationsLoaded(() => PosStore.prototype.pay.call(context));

    expect(dialogCalls.length).toBe(1);
    expect(dialogCalls[0].component).toBe(ConfirmationDialog);
    expect(dialogCalls[0].props.confirmLabel).toBe("Order");
    expect(dialogCalls[0].props.body.includes("Test Product")).toBe(true);
});

test("does not warn when every line is in stock", async () => {
    const lines = [
        makeLine("Test Product", {
            isRestrictProduct: true,
            qtyAvailable: 5,
            virtualAvailable: 5,
        }),
    ];
    const { context, dialogCalls } = makeContext("qty_on_hand", lines);

    await callIgnoringSuperErrors(context);

    expect(dialogCalls.length).toBe(0);
});

test("collects every out-of-stock line into the warning", async () => {
    const lines = [
        makeLine("Product A", { isRestrictProduct: true, qtyAvailable: 0, virtualAvailable: 0 }),
        makeLine("Product B", { isRestrictProduct: true, qtyAvailable: 5, virtualAvailable: 5 }),
        makeLine("Product C", { isRestrictProduct: true, qtyAvailable: 0, virtualAvailable: 0 }),
    ];
    const { context, dialogCalls } = makeContext("qty_on_hand", lines);

    await withTranslationsLoaded(() => PosStore.prototype.pay.call(context));

    expect(dialogCalls.length).toBe(1);
    expect(dialogCalls[0].props.body.includes("Product A")).toBe(true);
    expect(dialogCalls[0].props.body.includes("Product B")).toBe(false);
    expect(dialogCalls[0].props.body.includes("Product C")).toBe(true);
});

test("does not warn when restriction is disabled, even in virtual_qty mode", async () => {
    const lines = [
        makeLine("Test Product", {
            isRestrictProduct: false,
            qtyAvailable: 100,
            virtualAvailable: 0,
        }),
    ];
    const { context, dialogCalls } = makeContext("virtual_qty", lines);

    await withTranslationsLoaded(() => callIgnoringSuperErrors(context));

    expect(dialogCalls.length).toBe(0);
});

test("does not warn for a service product even if out of stock", async () => {
    const lines = [
        makeLine("Test Service", {
            isRestrictProduct: true,
            qtyAvailable: 0,
            virtualAvailable: 0,
            type: "service",
        }),
    ];
    const { context, dialogCalls } = makeContext("qty_on_hand", lines);

    await withTranslationsLoaded(() => callIgnoringSuperErrors(context));

    expect(dialogCalls.length).toBe(0);
});

test("does not warn for a to-be-weighed product even if out of stock", async () => {
    const lines = [
        makeLine("Test Weighed Product", {
            isRestrictProduct: true,
            qtyAvailable: 0,
            virtualAvailable: 0,
            toWeight: true,
        }),
    ];
    const { context, dialogCalls } = makeContext("qty_on_hand", lines);

    await withTranslationsLoaded(() => callIgnoringSuperErrors(context));

    expect(dialogCalls.length).toBe(0);
});
