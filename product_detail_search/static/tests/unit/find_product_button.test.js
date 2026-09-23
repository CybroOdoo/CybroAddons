/** @odoo-module */

import { expect, test } from "@odoo/hoot";
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
import { FindProductDialog } from "@product_detail_search/js/find_product";
import "@product_detail_search/js/find_product_button";

function makeContext() {
    const dialogCalls = [];
    return {
        context: {
            env: {
                services: {
                    dialog: {
                        add: (component, props) => dialogCalls.push({ component, props }),
                    },
                },
            },
        },
        dialogCalls,
    };
}

test("opens the Find Product dialog from the navbar", async () => {
    const { context, dialogCalls } = makeContext();

    await Navbar.prototype.find_product.call(context);

    expect(dialogCalls.length).toBe(1);
    expect(dialogCalls[0].component).toBe(FindProductDialog);
});
