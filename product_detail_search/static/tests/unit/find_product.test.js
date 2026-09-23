/** @odoo-module */

import { expect, test } from "@odoo/hoot";
import { FindProductDialog } from "@product_detail_search/js/find_product";

function makeContext(ormResult) {
    const ormCalls = [];
    return {
        context: {
            orm: {
                call: async (...args) => {
                    ormCalls.push(args);
                    return ormResult;
                },
            },
            state: { product_details: null },
        },
        ormCalls,
    };
}

test("stores the looked-up product details after a barcode scan", async () => {
    const details = [{ id: 1, display_name: "Test Product" }];
    const { context, ormCalls } = makeContext(details);

    await FindProductDialog.prototype._barcodeProductAction.call(context, {
        base_code: "1234567890",
    });

    expect(context.state.product_details).toBe(details);
    expect(ormCalls.length).toBe(1);
    expect(ormCalls[0][0]).toBe("product.template");
    expect(ormCalls[0][1]).toBe("product_detail_search");
    expect(ormCalls[0][2][1]).toBe("1234567890");
});

test("sets product_details to false when the barcode does not match a product", async () => {
    const { context } = makeContext(false);

    await FindProductDialog.prototype._barcodeProductAction.call(context, {
        base_code: "0000000000",
    });

    expect(context.state.product_details).toBe(false);
});

test("close() delegates to props.close", () => {
    let closed = false;
    const context = { props: { close: () => { closed = true; } } };

    FindProductDialog.prototype.close.call(context);

    expect(closed).toBe(true);
});

test("back() clears the scanned product details so the scan prompt reappears", () => {
    const context = { state: { product_details: { id: 1 } } };

    FindProductDialog.prototype.back.call(context);

    expect(context.state.product_details).toBe(false);
});
