import { describe, expect, test } from "@odoo/hoot";
import { mountWithCleanup } from "@web/../tests/web_test_helpers";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ConfirmationPopup } from "@simplified_pos/js/ConfirmationPopup";
import "@simplified_pos/js/ProductScreen";
import { session } from "@web/session";

const unpatchSelf = () => {
    const plugin = typeof odoo !== "undefined" && odoo.loader?.modules?.get("@pos_self_order/app/plugins/pos_data_plugin");
    if (plugin && typeof plugin.unpatchSelf === "function") {
        plugin.unpatchSelf();
    }
};

definePosModels();

async function createProductScreenEnv() {
    if (!session.data) {
        session.data = {};
    }
    session.data.config_id = 1;
    try {
        unpatchSelf();
    } catch {
        // ignore if already unpatched
    }
    const store = await setupPosEnv();
    const order = store.addNewOrder();
    const comp = await mountWithCleanup(ProductScreen, {
        props: { orderUuid: order.uuid },
    });
    return { store, order, comp };
}

describe("@simplified_pos > ProductScreen", () => {
    test("setup initializes dialog and popup references", async () => {
        const { comp } = await createProductScreenEnv();
        expect(Boolean(comp.dialog)).toBe(true);
        expect(comp.popup).toBe(comp.dialog);
    });

    test("payment_methods_from_config returns config payment methods or fallback", async () => {
        const { comp } = await createProductScreenEnv();
        expect(comp.payment_methods_from_config.length).toBeGreaterThan(0);
        expect(comp.payment_methods_from_config[0].model.name).toBe("pos.payment.method");

        const fakePos = { config: {} };
        const fallback = Object.getOwnPropertyDescriptor(
            ProductScreen.prototype,
            "payment_methods_from_config"
        ).get.call({ pos: fakePos });
        expect(fallback).toEqual([]);
    });

    test("customerDetails delegates to pos.selectPartner()", async () => {
        const { comp, store } = await createProductScreenEnv();
        let selectPartnerCalled = false;
        store.selectPartner = () => {
            selectPartnerCalled = true;
        };

        comp.customerDetails();
        expect(selectPartnerCalled).toBe(true);
    });

    describe("confirmOrder validation checks", () => {
        test("confirmOrder shows error dialog when cart is empty", async () => {
            const { comp } = await createProductScreenEnv();
            let openedDialog = null;
            let openedProps = null;

            comp.dialog = {
                add: (dialogComp, props) => {
                    openedDialog = dialogComp;
                    openedProps = props;
                },
            };

            Object.defineProperty(comp, "currentOrder", {
                value: {
                    lines: [],
                    partner_id: null,
                    getPartner: () => null,
                    payment_ids: [],
                },
                configurable: true,
            });

            comp.confirmOrder();

            expect(openedDialog).toBe(AlertDialog);
            expect(openedProps.body).toBe("Cart is empty.");
        });

        test("confirmOrder shows error dialog when customer is not selected", async () => {
            const { comp } = await createProductScreenEnv();
            let openedDialog = null;
            let openedProps = null;

            comp.dialog = {
                add: (dialogComp, props) => {
                    openedDialog = dialogComp;
                    openedProps = props;
                },
            };

            Object.defineProperty(comp, "currentOrder", {
                value: {
                    lines: [{ id: 1 }],
                    partner_id: null,
                    getPartner: () => null,
                    payment_ids: [],
                },
                configurable: true,
            });

            comp.confirmOrder();

            expect(openedDialog).toBe(AlertDialog);
            expect(openedProps.body).toBe("Select a Customer.");
        });

        test("confirmOrder shows error dialog when no payment line exists", async () => {
            const { comp } = await createProductScreenEnv();
            let openedDialog = null;
            let openedProps = null;

            comp.dialog = {
                add: (dialogComp, props) => {
                    openedDialog = dialogComp;
                    openedProps = props;
                },
            };

            Object.defineProperty(comp, "currentOrder", {
                value: {
                    lines: [{ id: 1 }],
                    partner_id: { id: 1, name: "Customer Test" },
                    payment_ids: [],
                },
                configurable: true,
            });

            comp.confirmOrder();

            expect(openedDialog).toBe(AlertDialog);
            expect(openedProps.body).toBe("Select a Payment Method");
        });

        test("confirmOrder opens ConfirmationPopup when order has lines, customer, and payment", async () => {
            const { comp } = await createProductScreenEnv();
            let openedDialog = null;
            let openedProps = null;

            comp.dialog = {
                add: (dialogComp, props) => {
                    openedDialog = dialogComp;
                    openedProps = props;
                },
            };

            Object.defineProperty(comp, "currentOrder", {
                value: {
                    lines: [{ id: 1 }],
                    partner_id: { id: 1, name: "Customer Test" },
                    payment_ids: [{ id: 1, amount: 100 }],
                },
                configurable: true,
            });

            comp.confirmOrder();

            expect(openedDialog).toBe(ConfirmationPopup);
            expect(openedProps.title).toBe("Confirmation");
        });
    });

    test("orderDone and _addNewOrder create a new order via pos.addNewOrder()", async () => {
        const { comp, store } = await createProductScreenEnv();
        let addNewOrderCount = 0;
        store.addNewOrder = () => {
            addNewOrderCount++;
        };

        comp._addNewOrder();
        expect(addNewOrderCount).toBe(1);

        comp.orderDone();
        expect(addNewOrderCount).toBe(2);
    });

    describe("addNewPaymentLine", () => {
        test("addNewPaymentLine resets numberBuffer and returns true on success", async () => {
            const { comp } = await createProductScreenEnv();
            let resetCalled = false;
            comp.numberBuffer = {
                reset: () => {
                    resetCalled = true;
                },
            };

            Object.defineProperty(comp, "currentOrder", {
                value: {
                    addPaymentline: () => ({ id: 10 }),
                },
                configurable: true,
            });

            const result = comp.addNewPaymentLine({ id: 1, name: "Cash" });
            expect(result).toBe(true);
            expect(resetCalled).toBe(true);
        });

        test("addNewPaymentLine shows AlertDialog and returns false on failure", async () => {
            const { comp } = await createProductScreenEnv();
            let openedDialog = null;
            let openedProps = null;
            comp.dialog = {
                add: (dialogComp, props) => {
                    openedDialog = dialogComp;
                    openedProps = props;
                },
            };

            Object.defineProperty(comp, "currentOrder", {
                value: {
                    addPaymentline: () => false,
                },
                configurable: true,
            });

            const result = comp.addNewPaymentLine({ id: 2, name: "Terminal" });
            expect(result).toBe(false);
            expect(openedDialog).toBe(AlertDialog);
            expect(openedProps.body).toBe("There is already an electronic payment in progress.");
        });
    });

    test("paymentLines and isRefundOrder getters reflect order state", async () => {
        const { comp } = await createProductScreenEnv();
        const mockOrder = {
            payment_ids: [{ id: 1 }, { id: 2 }],
            isRefund: true,
        };

        Object.defineProperty(comp, "currentOrder", {
            value: mockOrder,
            configurable: true,
        });

        expect(comp.paymentLines.length).toBe(2);
        expect(comp.isRefundOrder).toBe(true);

        mockOrder.isRefund = false;
        expect(comp.isRefundOrder).toBe(false);
    });

    describe("deletePaymentLine", () => {
        test("deletePaymentLine does nothing if line is not found", async () => {
            const { comp } = await createProductScreenEnv();
            let removeCalled = false;
            Object.defineProperty(comp, "currentOrder", {
                value: {
                    payment_ids: [],
                    removePaymentline: () => {
                        removeCalled = true;
                    },
                },
                configurable: true,
            });

            comp.deletePaymentLine("non-existent-uuid");
            expect(removeCalled).toBe(false);
        });

        test("deletePaymentLine removes qr_code payment line directly", async () => {
            const { comp } = await createProductScreenEnv();
            let removedLine = null;
            let resetCalled = false;
            comp.numberBuffer = {
                reset: () => {
                    resetCalled = true;
                },
            };

            const qrLine = {
                uuid: "qr-1",
                payment_method_id: { payment_method_type: "qr_code" },
            };

            Object.defineProperty(comp, "currentOrder", {
                value: {
                    payment_ids: [qrLine],
                    removePaymentline: (line) => {
                        removedLine = line;
                    },
                },
                configurable: true,
            });

            comp.deletePaymentLine("qr-1");
            expect(removedLine).toBe(qrLine);
            expect(resetCalled).toBe(true);
        });

        test("deletePaymentLine cancels via terminal when line is waiting", async () => {
            const { comp } = await createProductScreenEnv();
            let removedLine = null;
            let cancelCalledWith = null;

            comp.numberBuffer = { reset: () => {} };

            let status = "waiting";
            const terminalLine = {
                uuid: "term-1",
                getPaymentStatus: () => status,
                set_payment_status: (s) => {
                    status = s;
                },
                payment_method_id: {
                    payment_terminal: {
                        send_payment_cancel: async (ord, uuid) => {
                            cancelCalledWith = { ord, uuid };
                        },
                    },
                },
            };

            const mockOrder = {
                payment_ids: [terminalLine],
                removePaymentline: (line) => {
                    removedLine = line;
                },
            };

            Object.defineProperty(comp, "currentOrder", {
                value: mockOrder,
                configurable: true,
            });

            comp.deletePaymentLine("term-1");
            expect(status).toBe("waitingCancel");

            await Promise.resolve();
            await Promise.resolve();

            expect(cancelCalledWith).toEqual({ ord: mockOrder, uuid: "term-1" });
            expect(removedLine).toBe(terminalLine);
        });

        test("deletePaymentLine removes normal payment line if status !== waitingCancel", async () => {
            const { comp } = await createProductScreenEnv();
            let removedLine = null;
            comp.numberBuffer = { reset: () => {} };

            const normalLine = {
                uuid: "norm-1",
                getPaymentStatus: () => "pending",
                payment_method_id: {},
            };

            Object.defineProperty(comp, "currentOrder", {
                value: {
                    payment_ids: [normalLine],
                    removePaymentline: (line) => {
                        removedLine = line;
                    },
                },
                configurable: true,
            });

            comp.deletePaymentLine("norm-1");
            expect(removedLine).toBe(normalLine);
        });
    });

    test("selectPaymentLine sets selected_paymentline and resets buffer", async () => {
        const { comp } = await createProductScreenEnv();
        let resetCalled = false;
        comp.numberBuffer = {
            reset: () => {
                resetCalled = true;
            },
        };

        const targetLine = { uuid: "sel-1", amount: 50 };
        const mockOrder = {
            payment_ids: [targetLine],
            selected_paymentline: null,
        };

        Object.defineProperty(comp, "currentOrder", {
            value: mockOrder,
            configurable: true,
        });

        comp.selectPaymentLine("sel-1");
        expect(mockOrder.selected_paymentline).toBe(targetLine);
        expect(resetCalled).toBe(true);
    });

    test("sendForceDone and sendForceCancel call status methods on line", async () => {
        const { comp } = await createProductScreenEnv();
        let status = "";
        let forceCancelCalled = false;

        const dummyLine = {
            set_payment_status: (s) => {
                status = s;
            },
            forceCancel: () => {
                forceCancelCalled = true;
            },
        };

        await comp.sendForceDone(dummyLine);
        expect(status).toBe("done");

        await comp.sendForceCancel(dummyLine);
        expect(forceCancelCalled).toBe(true);
    });

    describe("sendPaymentReverse", () => {
        test("sendPaymentReverse returns early if no payment terminal", async () => {
            const { comp } = await createProductScreenEnv();
            const line = { payment_method_id: {} };
            await comp.sendPaymentReverse(line);
            expect(line.payment_status).toBe(undefined);
        });

        test("sendPaymentReverse sets amount 0 and status reversed on successful reversal", async () => {
            const { comp } = await createProductScreenEnv();
            let currentStatus = "";
            let currentAmount = 50;

            const line = {
                uuid: "rev-success",
                set_payment_status: (s) => {
                    currentStatus = s;
                },
                set_amount: (amt) => {
                    currentAmount = amt;
                },
                payment_method_id: {
                    payment_terminal: {
                        send_payment_reversal: async (uuid) => uuid === "rev-success",
                    },
                },
            };

            await comp.sendPaymentReverse(line);
            expect(currentStatus).toBe("reversed");
            expect(currentAmount).toBe(0);
        });

        test("sendPaymentReverse marks can_be_reversed false and status done on failed reversal", async () => {
            const { comp } = await createProductScreenEnv();
            let currentStatus = "";

            const line = {
                uuid: "rev-fail",
                can_be_reversed: true,
                set_payment_status: (s) => {
                    currentStatus = s;
                },
                payment_method_id: {
                    payment_terminal: {
                        send_payment_reversal: async () => false,
                    },
                },
            };

            await comp.sendPaymentReverse(line);
            expect(line.can_be_reversed).toBe(false);
            expect(currentStatus).toBe("done");
        });
    });

    describe("sendPaymentRequest", () => {
        test("sendPaymentRequest handles qr_code payment flow", async () => {
            const { comp, store } = await createProductScreenEnv();
            let captured = false;
            comp.numberBuffer = { capture: () => { captured = true; } };

            let showQRCalledWith = null;
            let responseHandledWith = null;

            store.showQR = async (line) => {
                showQRCalledWith = line;
                return { qr_result: "ok" };
            };

            const qrLine = {
                uuid: "qr-req",
                payment_method_id: { payment_method_type: "qr_code" },
                handle_payment_response: (resp) => {
                    responseHandledWith = resp;
                    return true;
                },
            };

            await comp.sendPaymentRequest(qrLine);

            expect(captured).toBe(true);
            expect(showQRCalledWith).toBe(qrLine);
            expect(responseHandledWith).toEqual({ qr_result: "ok" });
            expect(store.paymentTerminalInProgress).toBe(false);
        });

        test("sendPaymentRequest validates order when auto_validate_terminal_payment is enabled and order is paid", async () => {
            const { comp, store } = await createProductScreenEnv();
            comp.numberBuffer = { capture: () => {} };
            store.config.auto_validate_terminal_payment = true;

            let validatedOrder = false;
            comp.validateOrder = (arg) => {
                validatedOrder = true;
                expect(arg).toBe(false);
            };

            const mockOrder = {
                is_paid: () => true,
            };

            const termLine = {
                uuid: "term-req",
                pos_order_id: mockOrder,
                payment_method_id: { payment_method_type: "card" },
                pay: async () => true,
            };

            await comp.sendPaymentRequest(termLine);
            expect(validatedOrder).toBe(true);
        });
    });

    describe("updateSelectedPaymentline", () => {
        test("updateSelectedPaymentline auto adds paymentline if all lines are paid", async () => {
            const { comp } = await createProductScreenEnv();
            let addedPaymentMethod = null;

            Object.defineProperty(comp, "currentOrder", {
                value: {
                    payment_ids: [{ paid: true }],
                    add_paymentline: (pm) => {
                        addedPaymentMethod = pm;
                    },
                },
                configurable: true,
            });

            comp.updateSelectedPaymentline(25);
            expect(addedPaymentMethod).toBe(comp.payment_methods_from_config[0]);
        });

        test("updateSelectedPaymentline returns early when no selectedPaymentLine", async () => {
            const { comp } = await createProductScreenEnv();
            Object.defineProperty(comp, "currentOrder", {
                value: {
                    payment_ids: [{ paid: false }],
                    add_paymentline: () => {},
                },
                configurable: true,
            });
            comp.selectedPaymentLine = null;
            comp.updateSelectedPaymentline(50);
            expect(comp.selectedPaymentLine).toBe(null);
        });

        test("updateSelectedPaymentline deletes line when amount evaluates to null", async () => {
            const { comp } = await createProductScreenEnv();
            Object.defineProperty(comp, "currentOrder", {
                value: {
                    payment_ids: [{ paid: false }],
                    add_paymentline: () => {},
                },
                configurable: true,
            });
            let deletedUuid = null;
            comp.deletePaymentLine = (uuid) => {
                deletedUuid = uuid;
            };

            const line = {
                uuid: "line-to-delete",
                payment_method_id: {},
                getPaymentStatus: () => "pending",
            };
            comp.selectedPaymentLine = line;

            comp.updateSelectedPaymentline(null);
            expect(deletedUuid).toBe("line-to-delete");
        });

        test("updateSelectedPaymentline updates line amount when valid", async () => {
            const { comp } = await createProductScreenEnv();
            Object.defineProperty(comp, "currentOrder", {
                value: {
                    payment_ids: [{ paid: false }],
                    add_paymentline: () => {},
                },
                configurable: true,
            });
            let setAmt = null;
            const line = {
                uuid: "line-to-update",
                payment_method_id: {},
                getPaymentStatus: () => "pending",
                set_amount: (amt) => {
                    setAmt = amt;
                },
            };
            comp.selectedPaymentLine = line;

            comp.updateSelectedPaymentline(125.5);
            expect(setAmt).toBe(125.5);
        });
    });

    describe("sendPaymentCancel", () => {
        test("sendPaymentCancel returns early if no payment terminal exists", async () => {
            const { comp } = await createProductScreenEnv();
            const line = { payment_method_id: {} };
            await comp.sendPaymentCancel(line);
            expect(line.payment_status).toBe(undefined);
        });

        test("sendPaymentCancel sets retry on successful cancellation", async () => {
            const { comp } = await createProductScreenEnv();
            let status = "";
            const line = {
                uuid: "cancel-success",
                set_payment_status: (s) => {
                    status = s;
                },
                payment_method_id: {
                    payment_terminal: {
                        send_payment_cancel: async () => true,
                    },
                },
            };

            await comp.sendPaymentCancel(line);
            expect(status).toBe("retry");
        });

        test("sendPaymentCancel sets waitingCard on failed cancellation", async () => {
            const { comp } = await createProductScreenEnv();
            let status = "";
            const line = {
                uuid: "cancel-fail",
                set_payment_status: (s) => {
                    status = s;
                },
                payment_method_id: {
                    payment_terminal: {
                        send_payment_cancel: async () => false,
                    },
                },
            };

            await comp.sendPaymentCancel(line);
            expect(status).toBe("waitingCard");
        });
    });
});
