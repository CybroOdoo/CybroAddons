/** @odoo-module **/

import { expect, test } from "@odoo/hoot";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { translatedTerms, translationLoaded } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import "@pos_restrict_product_stock/js/ProductScreen";

function makeContext(config) {
    const dialogCalls = [];

    return {
        context: {
            pos: {
                config,
                addLineToCurrentOrder: async () => ({}),
            },

            dialog: {
                add: (component, props) => dialogCalls.push({ component, props }),
            },

            showOptionalProductPopupIfNeeded: async () => {},
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
 * Ignore failures from ProductScreen internals. We only care whether
 * our restriction logic executed correctly.
 */
async function callIgnoringSuperErrors(context, product) {
    try {
        return await ProductScreen.prototype.addProductToOrder.call(context, product);
    } catch {
        return undefined;
    }
}

test("warns before adding an out-of-stock product (qty_on_hand mode)", async () => {
    const { context, dialogCalls } = makeContext({
        is_restrict_product: true,
        stock_type: "qty_on_hand",
    });

    const product = {
        display_name: "Test Product",
        qty_available: 0,
        virtual_available: 100,
        type: "consu",
        to_weight: false,
    };

    await withTranslationsLoaded(() =>
        ProductScreen.prototype.addProductToOrder.call(context, product)
    );

    expect(dialogCalls.length).toBe(1);
    expect(dialogCalls[0].component).toBe(ConfirmationDialog);
    expect(dialogCalls[0].props.confirmLabel).toBe("Order");
    expect(dialogCalls[0].props.body.includes("Test Product")).toBe(true);
});

test("does not warn when the product is in stock (qty_on_hand mode)", async () => {
    const { context, dialogCalls } = makeContext({
        is_restrict_product: true,
        stock_type: "qty_on_hand",
    });

    const product = {
        display_name: "Test Product",
        qty_available: 5,
        virtual_available: 5,
        type: "consu",
        to_weight: false,
    };

    await callIgnoringSuperErrors(context, product);

    expect(dialogCalls.length).toBe(0);
});

test("confirming the dialog flags the product and re-attempts the order", async () => {
    const { context, dialogCalls } = makeContext({
        is_restrict_product: true,
        stock_type: "qty_on_hand",
    });

    const product = {
        display_name: "Test Product",
        qty_available: 0,
        virtual_available: 0,
        type: "consu",
        to_weight: false,
    };

    context.dialog.add = (component, props) => {
        dialogCalls.push({ component, props });
        props.confirm();
    };

    await withTranslationsLoaded(() =>
        ProductScreen.prototype.addProductToOrder.call(context, product)
    );

    expect(dialogCalls.length).toBe(1);
    expect(product.order_status).toBe(true);
});

test("does not warn when product restriction is disabled, even in virtual_qty mode", async () => {
    const { context, dialogCalls } = makeContext({
        is_restrict_product: false,
        stock_type: "virtual_qty",
    });

    const product = {
        display_name: "Test Product",
        qty_available: 100,
        virtual_available: 0,
        type: "consu",
        to_weight: false,
    };

    await withTranslationsLoaded(() =>
        callIgnoringSuperErrors(context, product)
    );

    expect(dialogCalls.length).toBe(0);
});

test("does not warn for a service product even if out of stock", async () => {
    const { context, dialogCalls } = makeContext({
        is_restrict_product: true,
        stock_type: "qty_on_hand",
    });

    const product = {
        display_name: "Test Service",
        qty_available: 0,
        virtual_available: 0,
        type: "service",
        to_weight: false,
    };

    await withTranslationsLoaded(() =>
        callIgnoringSuperErrors(context, product)
    );

    expect(dialogCalls.length).toBe(0);
});

test("does not warn for a to-be-weighed product even if out of stock", async () => {
    const { context, dialogCalls } = makeContext({
        is_restrict_product: true,
        stock_type: "qty_on_hand",
    });

    const product = {
        display_name: "Test Weighed Product",
        qty_available: 0,
        virtual_available: 0,
        type: "consu",
        to_weight: true,
    };

    await withTranslationsLoaded(() =>
        callIgnoringSuperErrors(context, product)
    );

    expect(dialogCalls.length).toBe(0);
});