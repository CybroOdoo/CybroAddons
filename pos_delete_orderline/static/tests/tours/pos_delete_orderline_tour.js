import * as Chrome from "@point_of_sale/../tests/pos/tours/utils/chrome_util";
import * as Combo from "@point_of_sale/../tests/pos/tours/utils/combo_popup_util";
import * as Dialog from "@point_of_sale/../tests/generic_helpers/dialog_util";
import * as Order from "@point_of_sale/../tests/generic_helpers/order_widget_util";
import * as ProductScreen from "@point_of_sale/../tests/pos/tours/utils/product_screen_util";
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("pos_delete_orderline_tour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.addOrderline("Desk Pad", "1"),
            ProductScreen.addOrderline("Letter Tray", "2"),
            {
                content: "Remove the Desk Pad line with its delete button",
                trigger: `.orderline:has(.product-name:contains("Desk Pad")) .o_pos_delete_orderline_btn`,
                run: "click",
            },
            Order.doesNotHaveLine({ productName: "Desk Pad" }),
            Order.hasLine({ productName: "Letter Tray", quantity: "2" }),
            ProductScreen.addOrderline("Desk Pad", "1"),
            {
                content: "Open Clear All confirmation",
                trigger: ".o_pos_clear_lines_btn",
                run: "click",
            },
            Dialog.cancel({ title: "Clear all lines?" }),
            Order.hasLine({ productName: "Desk Pad", quantity: "1" }),
            {
                content: "Clear all lines",
                trigger: ".o_pos_clear_lines_btn",
                run: "click",
            },
            Dialog.confirm("Clear"),
            ProductScreen.orderIsEmpty(),
            {
                content: "Clear All is disabled on an empty order",
                trigger: ".o_pos_clear_lines_btn:disabled",
            },
            ...ProductScreen.clickDisplayedProduct("Delete Test Combo"),
            Combo.select("Combo Product 1"),
            Dialog.confirm(),
            {
                content: "Remove a combo through one of its component lines",
                trigger: `.orderline:has(.product-name:contains("Combo Product 1")) .o_pos_delete_orderline_btn`,
                run: "click",
            },
            Order.doesNotHaveLine(),
        ].flat(),
});
