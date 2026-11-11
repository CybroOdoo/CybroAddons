import * as Dialog from "@point_of_sale/../tests/generic_helpers/dialog_util";
import * as Chrome from "@point_of_sale/../tests/pos/tours/utils/chrome_util";
import * as PaymentScreen from "@point_of_sale/../tests/pos/tours/utils/payment_screen_util";
import * as ProductScreen from "@point_of_sale/../tests/pos/tours/utils/product_screen_util";
import * as ReceiptScreen from "@point_of_sale/../tests/pos/tours/utils/receipt_screen_util";
import * as FloorScreen from "@pos_restaurant/../tests/tours/utils/floor_screen_util";
import { registry } from "@web/core/registry";

const takeAwayButton = ".product-screen .pos_takeaway_button";

function clickTakeAway() {
    return [{ content: "click the Take Away button", trigger: takeAwayButton, run: "click" }];
}

function takeAwayIsActive(active) {
    const state = active ? ".btn-primary" : ".btn-light";
    return [{ content: `Take Away button is ${active ? "on" : "off"}`, trigger: takeAwayButton + state }];
}

function payWithBank() {
    return [
        ProductScreen.clickPayButton(),
        PaymentScreen.clickPaymentMethod("Bank"),
        PaymentScreen.clickValidate(),
        ReceiptScreen.isShown(),
    ].flat();
}

registry.category("web_tour.tours").add("PosTakeAwayTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),

            // Take Away order: the receipt shows the label and the token.
            FloorScreen.clickTable("2"),
            takeAwayIsActive(false),
            // The button warns when the order is empty and stays off.
            clickTakeAway(),
            {
                content: "a warning asks to add a product first",
                trigger: ".o_notification:contains('Please add a product first.')",
            },
            takeAwayIsActive(false),
            ProductScreen.clickDisplayedProduct("Water"),
            clickTakeAway(),
            takeAwayIsActive(true),
            payWithBank(),
            {
                content: "the receipt is labelled Take Away",
                trigger: ".pos-receipt .pos_takeaway_order_type:contains('Take Away')",
            },
            {
                content: "the receipt shows the token issued by the server",
                trigger: ".pos-receipt .pos_takeaway_token:contains('Token Number: 1')",
            },
            ReceiptScreen.clickNextOrder(),

            // Switching back to Dine-In: no token and a Dine-In label.
            FloorScreen.clickTable("4"),
            ProductScreen.clickDisplayedProduct("Coca-Cola"),
            clickTakeAway(),
            takeAwayIsActive(true),
            clickTakeAway(),
            takeAwayIsActive(false),
            payWithBank(),
            {
                content: "the receipt is labelled Dine-In",
                trigger: ".pos-receipt .pos_takeaway_order_type:contains('Dine-In')",
            },
            {
                content: "a Dine-In receipt has no token",
                trigger: ".pos-receipt:not(:has(.pos_takeaway_token))",
            },
            ReceiptScreen.clickNextOrder(),
        ].flat(),
});

registry.category("web_tour.tours").add("PosTakeAwayHiddenTour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            FloorScreen.clickTable("2"),
            ProductScreen.clickDisplayedProduct("Water"),
            {
                content: "the Take Away button is not shown",
                trigger: ".product-screen:not(:has(.pos_takeaway_button))",
            },
        ].flat(),
});
