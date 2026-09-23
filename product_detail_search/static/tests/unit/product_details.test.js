/** @odoo-module */

import { expect, test } from "@odoo/hoot";
import { ProductDetails } from "@product_detail_search/js/product_details";

test("setup() reads the initial product details from props", () => {
    const context = { props: { product_details: [{ id: 7 }] } };

    ProductDetails.prototype.setup.call(context);

    expect(context.product_details).toBe(context.props.product_details);
});

test("setup() defaults to false when no product details are provided", () => {
    const context = { props: {} };

    ProductDetails.prototype.setup.call(context);

    expect(context.product_details).toBe(false);
});

test("back() clears the product details on props so the scan prompt reappears", () => {
    const context = { props: { product_details: [{ id: 1 }] } };

    ProductDetails.prototype.back.call(context);

    expect(context.props.product_details).toBe(false);
});
