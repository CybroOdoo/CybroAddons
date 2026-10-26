import { registry } from "@web/core/registry";
import * as Chrome from "@point_of_sale/../tests/pos/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/generic_helpers/dialog_util";
import * as ProductScreen from "@point_of_sale/../tests/pos/tours/utils/product_screen_util";

registry.category("web_tour.tours").add("carry_bag_pos_tour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            {
                content: "Click on the Add Bag button",
                trigger: "button:contains('Add Bag')",
                run: "click",
            },
            {
                content: "The bag of the configured category is listed with its stock on hand",
                trigger: ".o_bag_popup_list .o_bag_item:contains('Test Carry Bag') .o_bag_item_stock:contains('0')",
            },
            {
                content: "Other categories are not listed",
                trigger: ".o_bag_popup_list:not(:has(.o_bag_item:contains('Test Other Product')))",
            },
            {
                content: "Select the bag",
                trigger: ".o_bag_popup_list .o_bag_item:contains('Test Carry Bag')",
                run: "click",
            },
            ProductScreen.selectedOrderlineHas("Test Carry Bag", "1", "0.50"),
        ].flat(),
});
