/** @odoo-module **/

import { expect, test } from "@odoo/hoot";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { translatedTerms, translationLoaded } from "@web/core/l10n/translation";
import { ProductConfiguratorPopup } from "@point_of_sale/app/components/popups/product_configurator_popup/product_configurator_popup";
import "@pos_restrict_product_stock/js/ProductConfiguratorPopup";

function makeContext({ product, isRestrictProduct, stockType }) {
    const dialogCalls = [];
    return {
        context: {
            product,
            pos: { config: { is_restrict_product: isRestrictProduct, stock_type: stockType } },
            env: {
                services: {
                    dialog: {
                        add: (component, props) => {
                            dialogCalls.push({ component, props });
                        },
                    },
                },
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
 * Calling the real super.confirm() needs the popup's full component
 * internals (env, props, services) that we don't stub here, so any branch
 * that reaches it is expected to throw in this lightweight setup. We only
 * care whether the out-of-stock dialog was shown before that point.
 */
async function callConfirmIgnoringSuperErrors(context) {
    return withTranslationsLoaded(async () => {
        try {
            return await ProductConfiguratorPopup.prototype.confirm.call(context, {});
        } catch {
            return undefined;
        }
    });
}

test("skips the stock check entirely when there is no product", async () => {
    const { context, dialogCalls } = makeContext({
        product: null,
        isRestrictProduct: true,
        stockType: "qty_on_hand",
    });

    await callConfirmIgnoringSuperErrors(context);

    expect(dialogCalls.length).toBe(0);
});

test("skips the stock check when product restriction is disabled", async () => {
    const { context, dialogCalls } = makeContext({
        product: { display_name: "Test Product", qty_available: 0, virtual_available: 0 },
        isRestrictProduct: false,
        stockType: "qty_on_hand",
    });

    await callConfirmIgnoringSuperErrors(context);

    expect(dialogCalls.length).toBe(0);
});

test("qty_on_hand mode warns when qty_available is out of stock", async () => {
    const { context, dialogCalls } = makeContext({
        product: { display_name: "Test Product", qty_available: 0, virtual_available: 100 },
        isRestrictProduct: true,
        stockType: "qty_on_hand",
    });
    context.env.services.dialog.add = (component, props) => {
        dialogCalls.push({ component, props });
        props.cancel();
    };

    const result = await withTranslationsLoaded(() =>
        ProductConfiguratorPopup.prototype.confirm.call(context, {})
    );

    expect(dialogCalls.length).toBe(1);
    expect(dialogCalls[0].component).toBe(ConfirmationDialog);
    expect(dialogCalls[0].props.title).toBe("Out of Stock");
    expect(dialogCalls[0].props.body).toBe("Test Product is out of stock. Do you want to proceed?");
    // Cancelling returns without ever reaching super.confirm().
    expect(result).toBe(undefined);
});

test("qty_on_hand mode ignores virtual_available", async () => {
    const { context, dialogCalls } = makeContext({
        product: { display_name: "Test Product", qty_available: 5, virtual_available: 0 },
        isRestrictProduct: true,
        stockType: "qty_on_hand",
    });

    await callConfirmIgnoringSuperErrors(context);

    expect(dialogCalls.length).toBe(0);
});

test("virtual_qty mode warns when virtual_available is out of stock", async () => {
    const { context, dialogCalls } = makeContext({
        product: { display_name: "Test Product", qty_available: 100, virtual_available: 0 },
        isRestrictProduct: true,
        stockType: "virtual_qty",
    });
    context.env.services.dialog.add = (component, props) => {
        dialogCalls.push({ component, props });
        props.cancel();
    };

    await withTranslationsLoaded(() =>
        ProductConfiguratorPopup.prototype.confirm.call(context, {})
    );

    expect(dialogCalls.length).toBe(1);
});

test("virtual_qty mode ignores qty_available", async () => {
    const { context, dialogCalls } = makeContext({
        product: { display_name: "Test Product", qty_available: 0, virtual_available: 5 },
        isRestrictProduct: true,
        stockType: "virtual_qty",
    });

    await callConfirmIgnoringSuperErrors(context);

    expect(dialogCalls.length).toBe(0);
});

test("both mode warns when either quantity is out of stock", async () => {
    const { context, dialogCalls } = makeContext({
        product: { display_name: "Test Product", qty_available: 0, virtual_available: 5 },
        isRestrictProduct: true,
        stockType: "both",
    });
    context.env.services.dialog.add = (component, props) => {
        dialogCalls.push({ component, props });
        props.cancel();
    };

    await withTranslationsLoaded(() =>
        ProductConfiguratorPopup.prototype.confirm.call(context, {})
    );

    expect(dialogCalls.length).toBe(1);
});

test("both mode does not warn when both quantities are available", async () => {
    const { context, dialogCalls } = makeContext({
        product: { display_name: "Test Product", qty_available: 5, virtual_available: 5 },
        isRestrictProduct: true,
        stockType: "both",
    });

    await callConfirmIgnoringSuperErrors(context);

    expect(dialogCalls.length).toBe(0);
});
