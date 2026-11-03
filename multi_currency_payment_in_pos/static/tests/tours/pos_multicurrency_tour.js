import * as Chrome from "@point_of_sale/../tests/pos/tours/utils/chrome_util";
import * as Dialog from "@point_of_sale/../tests/generic_helpers/dialog_util";
import * as ProductScreen from "@point_of_sale/../tests/pos/tours/utils/product_screen_util";
import * as PaymentScreen from "@point_of_sale/../tests/pos/tours/utils/payment_screen_util";
import * as FeedbackScreen from "@point_of_sale/../tests/pos/tours/utils/feedback_screen_util";
import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("pos_multicurrency_payment_tour", {
    steps: () =>
        [
            Chrome.startPoS(),
            Dialog.confirm("Open Register"),
            ProductScreen.clickDisplayedProduct("Payment Test Product"),
            ProductScreen.clickPayButton(),
            PaymentScreen.isShown(),
            {
                content: "Enable multi-currency option",
                trigger: "#multi_currency_check",
                run: "click",
            },
            {
                content: "Select EUR currency",
                trigger: ".currency_list",
                run: "selectByLabel EUR",
            },
            {
                content: "Verify displayed exchange rate (1 USD = 1.1 EUR)",
                trigger: ".mc-line .usdamount:contains('1.1')",
            },
            {
                content: "Verify converted total amount in conversion box (55 €)",
                trigger: ".mc-line .total_amount:contains('55')",
            },
            {
                content: "Add foreign currency payment",
                trigger: ".mc-addpayment",
                run: "click",
            },
            {
                content: "Verify Cash payment method is selected on the payment line",
                trigger: ".paymentlines .paymentline .payment-name:contains('Cash')",
            },
            {
                content: "Verify payment amount in POS currency is 50.00",
                trigger: ".paymentlines .paymentline .payment-amount:contains('50.00')",
            },
            {
                content: "Verify foreign currency amount and symbol are displayed on payment line",
                trigger: ".payment-currency:contains('55'):contains('€')",
            },
            {
                content: "Switch dropdown currency to USD",
                trigger: ".currency_list",
                run: "selectByLabel USD",
            },
            {
                content: "Click payment line to trigger selection / update check",
                trigger: ".paymentlines .paymentline",
                run: "click",
            },
            {
                content: "Verify payment line retains its own EUR currency symbol and amount",
                trigger: ".payment-currency:contains('55'):contains('€')",
            },
            PaymentScreen.clickValidate(),
            FeedbackScreen.isShown(),
        ].flat(),
});
