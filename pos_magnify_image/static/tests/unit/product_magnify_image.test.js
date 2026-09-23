/** @odoo-module **/

import { expect, test } from "@odoo/hoot";
import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { MagnifyProductPopup } from "@pos_magnify_image/js/MagnifyProductPopup";
import "@pos_magnify_image/js/prouct_magnify_image";

function makeCard(product) {
    const added = [];
    const card = {
        props: { product },
        dialog: { add: (component, props) => added.push({ component, props }) },
    };
    return { card, added };
}

/**
 * The patched onProductMagnifyClick intentionally logs via console.error
 * when it bails out early (no product / no id). Hoot treats any
 * console.error call as an unexpected failure, so we stub it out for the
 * duration of the callback and restore it afterwards.
 */
async function withSuppressedConsoleError(callback) {
    const originalConsoleError = console.error;
    console.error = () => {};
    try {
        return await callback();
    } finally {
        console.error = originalConsoleError;
    }
}

test("clicking the magnify icon opens the popup with the product", async () => {
    const product = { id: 42, name: "Test Product" };
    const { card, added } = makeCard(product);

    await ProductCard.prototype.onProductMagnifyClick.call(card, {});

    expect(added.length).toBe(1);
    expect(added[0].component).toBe(MagnifyProductPopup);
    expect(added[0].props).toEqual({ product });
});

test("clicking the magnify icon does nothing when the product has no id", async () => {
    const { card, added } = makeCard({ name: "No Id Product" });

    await withSuppressedConsoleError(() =>
        ProductCard.prototype.onProductMagnifyClick.call(card, {})
    );

    expect(added.length).toBe(0);
});

test("clicking the magnify icon does nothing when there is no product on the card", async () => {
    const { card, added } = makeCard(undefined);

    await withSuppressedConsoleError(() =>
        ProductCard.prototype.onProductMagnifyClick.call(card, {})
    );

    expect(added.length).toBe(0);
});
