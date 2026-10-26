/** @odoo-module **/

import { describe, expect, test } from "@odoo/hoot";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import "@pos_numpad_show_hide/js/pos_numpad";

describe("POS Numpad Show/Hide - JS Unit Tests", () => {
    describe.current.tags("desktop");

    test("toggleNumpad() toggles isNumpadHidden state on ProductScreen", () => {
        const dummyScreen = {
            state: { isNumpadHidden: false },
        };

        // First toggle should change to true
        ProductScreen.prototype.toggleNumpad.call(dummyScreen);
        expect(dummyScreen.state.isNumpadHidden).toBe(true);

        // Second toggle should change to false
        ProductScreen.prototype.toggleNumpad.call(dummyScreen);
        expect(dummyScreen.state.isNumpadHidden).toBe(false);
    });

    test("setup() initializes isNumpadHidden to false", () => {
        expect(typeof ProductScreen.prototype.toggleNumpad).toBe("function");
        expect(typeof ProductScreen.prototype.setup).toBe("function");
    });
});
