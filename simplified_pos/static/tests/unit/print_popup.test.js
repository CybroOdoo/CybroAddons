import { describe, expect, test } from "@odoo/hoot";
import { mountWithCleanup, patchWithCleanup } from "@web/../tests/web_test_helpers";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { PrintPopup } from "@simplified_pos/js/PrintPopup";
import { session } from "@web/session";

const unpatchSelf = () => {
    const plugin = typeof odoo !== "undefined" && odoo.loader?.modules?.get("@pos_self_order/app/plugins/pos_data_plugin");
    if (plugin && typeof plugin.unpatchSelf === "function") {
        plugin.unpatchSelf();
    }
};

definePosModels();

const initPosEnv = async () => {
    if (!session.data) {
        session.data = {};
    }
    session.data.config_id = 1;
    try {
        unpatchSelf();
    } catch {
        // ignore if already unpatched
    }
    return await setupPosEnv();
};

describe("@simplified_pos > PrintPopup", () => {
    test("setup initializes pos instance", async () => {
        const store = await initPosEnv();
        const popup = await mountWithCleanup(PrintPopup, {
            props: { close: () => {} },
        });

        expect(popup.pos).toBe(store);
    });

    test("currentOrder getter prefers props.orderToPrint over pos.getOrder()", async () => {
        const store = await initPosEnv();
        const activeOrder = store.addNewOrder();
        const customOrder = { id: 99, name: "Custom Printed Order" };

        const popupWithProp = await mountWithCleanup(PrintPopup, {
            props: { orderToPrint: customOrder, close: () => {} },
        });
        expect(popupWithProp.currentOrder).toBe(customOrder);

        const popupWithoutProp = await mountWithCleanup(PrintPopup, {
            props: { close: () => {} },
        });
        expect(popupWithoutProp.currentOrder).toBe(activeOrder);
    });

    test("finishOrder creates a new order if current order is paid or null", async () => {
        await initPosEnv();
        let addNewOrderCalled = false;
        const fakePos = {
            addNewOrder: () => {
                addNewOrderCalled = true;
            },
        };

        const paidOrder = { state: "paid" };
        const popup = await mountWithCleanup(PrintPopup, {
            props: { orderToPrint: paidOrder, close: () => {} },
        });
        popup.pos = fakePos;

        popup.finishOrder();
        expect(addNewOrderCalled).toBe(true);
    });

    test("finishOrder does not create a new order if current order is unpaid", async () => {
        await initPosEnv();
        let addNewOrderCalled = false;
        const fakePos = {
            getOrder: () => ({ state: "draft" }),
            addNewOrder: () => {
                addNewOrderCalled = true;
            },
        };

        const popup = await mountWithCleanup(PrintPopup, {
            props: { close: () => {} },
        });
        popup.pos = fakePos;

        popup.finishOrder();
        expect(addNewOrderCalled).toBe(false);
    });

    test("cancel closes popup and invokes finishOrder", async () => {
        await initPosEnv();
        let closeCalled = false;
        let finishOrderCalled = false;

        const popup = await mountWithCleanup(PrintPopup, {
            props: {
                close: () => {
                    closeCalled = true;
                },
            },
        });

        popup.finishOrder = () => {
            finishOrderCalled = true;
        };

        await popup.cancel();
        expect(closeCalled).toBe(true);
        expect(finishOrderCalled).toBe(true);
    });

    test("printReceipt closes and finishes order if no content is found", async () => {
        await initPosEnv();
        let closeCalled = false;
        let finishOrderCalled = false;

        const popup = await mountWithCleanup(PrintPopup, {
            props: {
                close: () => {
                    closeCalled = true;
                },
            },
        });

        popup.finishOrder = () => {
            finishOrderCalled = true;
        };

        popup.receiptRef = { el: null };

        await popup.printReceipt();
        expect(closeCalled).toBe(true);
        expect(finishOrderCalled).toBe(true);
    });

    test("printReceipt opens window, writes receipt HTML, and triggers printing", async () => {
        await initPosEnv();
        let closeCalled = false;
        let finishOrderCalled = false;
        let writtenHtml = "";
        let windowOpened = false;

        const mockWindow = {
            document: {
                write: (html) => {
                    writtenHtml += html;
                },
                close: () => {},
            },
            focus: () => {},
            print: () => {},
            close: () => {},
        };

        patchWithCleanup(window, {
            open: () => {
                windowOpened = true;
                return mockWindow;
            },
        });

        const popup = await mountWithCleanup(PrintPopup, {
            props: {
                close: () => {
                    closeCalled = true;
                },
            },
        });

        popup.finishOrder = () => {
            finishOrderCalled = true;
        };

        popup.receiptRef = {
            el: { innerHTML: "<div class='receipt-test'>Order Receipt Content</div>" },
        };

        await popup.printReceipt();

        expect(windowOpened).toBe(true);
        expect(writtenHtml).toInclude("Order Receipt Content");
        expect(writtenHtml).toInclude("<title>Print Receipt</title>");
    });

    test("orderlines getter extracts product name, qty, raw price, and formatted price", async () => {
        const store = await initPosEnv();
        const testOrder = {
            lines: [
                {
                    product_id: { display_name: "Espresso" },
                    qty: 2,
                    price_subtotal_incl: 10.0,
                },
                {
                    full_product_name: "Croissant",
                    get_quantity: () => 3,
                    get_all_prices: () => ({ priceWithTax: 15.0 }),
                },
            ],
        };

        store.format_currency = (val) => `$ ${Number(val).toFixed(2)}`;

        const popup = await mountWithCleanup(PrintPopup, {
            props: { orderToPrint: testOrder, close: () => {} },
        });

        const lines = popup.orderlines;
        expect(lines.length).toBe(2);
        expect(lines[0][0]).toBe("Espresso");
        expect(lines[0][1]).toBe(2);
        expect(lines[0][2]).toBe(10.0);
        expect(lines[0][3]).toBe("$ 10.00");

        expect(lines[1][0]).toBe("Croissant");
        expect(lines[1][1]).toBe(3);
        expect(lines[1][2]).toBe(15.0);
        expect(lines[1][3]).toBe("$ 15.00");
    });

    test("orderlines returns empty array when order is missing", async () => {
        await initPosEnv();
        const popup = await mountWithCleanup(PrintPopup, {
            props: { close: () => {} },
        });
        popup.pos.getOrder = () => null;

        expect(popup.orderlines).toEqual([]);
    });

    test("total getter calculates total from order or payment lines", async () => {
        const store = await initPosEnv();
        store.format_currency = (val) => `$ ${Number(val).toFixed(2)}`;

        // Total via amount_total
        const orderWithAmount = {
            amount_total: 45.5,
        };
        const popup1 = await mountWithCleanup(PrintPopup, {
            props: { orderToPrint: orderWithAmount, close: () => {} },
        });
        expect(popup1.total).toBe("$ 45.50");

        // Total via payments fallback when amount is 0
        const orderWithPayments = {
            amount_total: 0,
            payment_ids: [{ amount: 20 }, { amount: 30 }],
        };
        const popup2 = await mountWithCleanup(PrintPopup, {
            props: { orderToPrint: orderWithPayments, close: () => {} },
        });
        expect(popup2.total).toBe("$ 50.00");

        // No order returns default 0.00
        const popup3 = await mountWithCleanup(PrintPopup, {
            props: { close: () => {} },
        });
        popup3.pos.getOrder = () => null;
        expect(popup3.total).toBe("0.00");
    });

    test("cashierName getter retrieves cashier name from pos", async () => {
        const store = await initPosEnv();
        store.user = { name: "Mitchell Admin" };

        const popup = await mountWithCleanup(PrintPopup, {
            props: { close: () => {} },
        });

        expect(popup.cashierName).toBe("Mitchell Admin");
    });
});
