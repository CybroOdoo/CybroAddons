/** @odoo-module */

import * as Chrome from "@point_of_sale/../tests/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/tours/utils/dialog_util";
import * as ProductScreen from "@point_of_sale/../tests/tours/utils/product_screen_util";
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("PosButtonVisibilityTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.addOrderline("Desk Organizer", "1"),
            {
                content: "Quantity numpad button is still available",
                trigger: ".numpad button.numpad-qty:not([disabled])",
            },
            {
                content: "Discount numpad button is disabled",
                trigger: ".numpad button.numpad-discount[disabled]",
            },
            {
                content: "Price numpad button is disabled",
                trigger: ".numpad button.numpad-price[disabled]",
            },
            ProductScreen.clickControlButtonMore(),
            {
                content: "Refund button is disabled",
                trigger: '.control-buttons button[disabled]:contains("Refund")',
            },
            Chrome.endTour(),
        ].flat(),
});
