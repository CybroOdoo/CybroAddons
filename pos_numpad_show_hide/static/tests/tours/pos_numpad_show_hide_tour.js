/** @odoo-module **/

import { registry } from "@web/core/registry";
import * as Chrome from "@point_of_sale/../tests/pos/tours/utils/chrome_util";
import * as ProductScreen from "@point_of_sale/../tests/pos/tours/utils/product_screen_util";
import * as Dialog from "@point_of_sale/../tests/generic_helpers/dialog_util";

registry.category("web_tour.tours").add("pos_numpad_show_hide_tour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.isShown(),
            {
                content: "Verify toggle numpad button is visible",
                trigger: ".pos-numpad-toggle-button",
            },
            {
                content: "Verify initial eye icon is visibility",
                trigger: ".pos-numpad-toggle-button [data-icon='visibility']",
            },
            {
                content: "Click toggle numpad button to hide",
                trigger: ".pos-numpad-toggle-button",
                run: "click",
            },
            {
                content: "Verify toggle icon changes to visibility_off",
                trigger: ".pos-numpad-toggle-button [data-icon='visibility_off']",
            },
            {
                content: "Click toggle numpad button to show",
                trigger: ".pos-numpad-toggle-button",
                run: "click",
            },
            {
                content: "Verify toggle icon changes back to visibility",
                trigger: ".pos-numpad-toggle-button [data-icon='visibility']",
            },
        ].flat(),
});
