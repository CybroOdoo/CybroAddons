import { describe, expect, test } from "@odoo/hoot";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { onRpc, mountWithCleanup, patchWithCleanup } from "@web/../tests/web_test_helpers";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";

definePosModels();

const setupPaidOrder = async (store) => {
    const order = store.addNewOrder();
    await store.addLineToOrder(
        { product_tmpl_id: store.models["product.template"].get(5), qty: 1 },
        order
    );
    order.state = "paid";
    return order;
};

describe("pos_refund_password", () => {
    test("onDoRefund calls super without prompting password when has_refund_password is false", async () => {
        const store = await setupPosEnv();
        store.config.has_refund_password = false;

        const order = await setupPaidOrder(store);
        const comp = await mountWithCleanup(TicketScreen, { props: {} });
        comp.setSelectedOrder(order);

        let dialogOpened = false;
        patchWithCleanup(comp.dialog, {
            add: () => {
                dialogOpened = true;
            },
        });

        await comp.onDoRefund();

        expect(dialogOpened).toBe(false);
    });

    test("onDoRefund prompts for password and completes refund when correct", async () => {
        const store = await setupPosEnv();
        store.config.has_refund_password = true;

        const order = await setupPaidOrder(store);
        const comp = await mountWithCleanup(TicketScreen, { props: {} });
        comp.setSelectedOrder(order);

        let dialogTitle = "";
        let rpcCalledWith = null;

        patchWithCleanup(comp.dialog, {
            add: (_component, props) => {
                dialogTitle = props.title?.toString() || "";
                props.getPayload?.("1234");
                props.close?.();
            },
        });

        onRpc("pos.config", "verify_refund_password", ({ args }) => {
            rpcCalledWith = args;
            return true;
        });

        await comp.onDoRefund();

        expect(dialogTitle).toBe("Confirm Password");
        expect(rpcCalledWith[0]).toEqual([store.config.id]);
        expect(rpcCalledWith[1]).toBe("1234");
    });

    test("onDoRefund shows warning notification and halts when password is wrong", async () => {
        const store = await setupPosEnv();
        store.config.has_refund_password = true;

        const order = await setupPaidOrder(store);
        const comp = await mountWithCleanup(TicketScreen, { props: {} });
        comp.setSelectedOrder(order);

        let notificationAdded = false;

        patchWithCleanup(comp.dialog, {
            add: (_component, props) => {
                props.getPayload?.("wrong_pass");
                props.close?.();
            },
        });

        patchWithCleanup(comp.env.services.notification, {
            add: (message, options) => {
                notificationAdded = true;
                expect(options.type).toBe("warning");
            },
        });

        onRpc("pos.config", "verify_refund_password", () => false);

        await comp.onDoRefund();

        expect(notificationAdded).toBe(true);
    });

    test("onDoRefund cancels gracefully when password dialog is dismissed", async () => {
        const store = await setupPosEnv();
        store.config.has_refund_password = true;

        const order = await setupPaidOrder(store);
        const comp = await mountWithCleanup(TicketScreen, { props: {} });
        comp.setSelectedOrder(order);

        let rpcCalled = false;

        patchWithCleanup(comp.dialog, {
            add: (_component, props, options) => {
                // User closes modal without submitting payload
                if (options?.onClose) {
                    options.onClose();
                } else if (props.getPayload) {
                    props.getPayload(null);
                }
            },
        });

        onRpc("pos.config", "verify_refund_password", () => {
            rpcCalled = true;
            return true;
        });

        await comp.onDoRefund();

        expect(rpcCalled).toBe(false);
    });
});
