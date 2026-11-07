import { describe, expect, test } from "@odoo/hoot";
import { mountWithCleanup } from "@web/../tests/web_test_helpers";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { ConfirmationPopup } from "@simplified_pos/js/ConfirmationPopup";
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

describe("@simplified_pos > ConfirmationPopup", () => {
    test("setup initializes pos and dialog services", async () => {
        const store = await initPosEnv();
        const popup = await mountWithCleanup(ConfirmationPopup, {
            props: {
                title: "Test Confirmation",
                close: () => {},
            },
        });

        expect(popup.pos).toBe(store);
        expect(Boolean(popup.dialog)).toBe(true);
    });

    test("finalizeOrder does nothing when order is undefined or null", async () => {
        const store = await initPosEnv();
        let addPendingCalled = false;
        store.addPendingOrder = () => {
            addPendingCalled = true;
        };

        const popup = await mountWithCleanup(ConfirmationPopup, {
            props: { close: () => {} },
        });

        await popup.finalizeOrder(null);
        await popup.finalizeOrder(undefined);

        expect(addPendingCalled).toBe(false);
    });

    test("finalizeOrder does not re-finalize or sync if order state is already paid", async () => {
        const store = await initPosEnv();
        let syncCalled = false;
        store.syncAllOrders = async () => {
            syncCalled = true;
        };

        const popup = await mountWithCleanup(ConfirmationPopup, {
            props: { close: () => {} },
        });

        const order = { id: 10, uuid: "uuid-10", state: "paid" };
        await popup.finalizeOrder(order);

        expect(syncCalled).toBe(false);
        expect(order.state).toBe("paid");
    });

    test("finalizeOrder marks order as paid, adds to pending, tracks unsynced uuid, and syncs", async () => {
        const store = await initPosEnv();
        let pendingOrderIds = null;
        let syncOptions = null;
        const unsyncedSet = new Set();

        store.addPendingOrder = (ids) => {
            pendingOrderIds = ids;
        };
        store.syncAllOrders = async (options) => {
            syncOptions = options;
        };
        store.data = {
            localUnsyncedPaidOrderUuids: unsyncedSet,
        };

        const popup = await mountWithCleanup(ConfirmationPopup, {
            props: { close: () => {} },
        });

        const order = { id: 42, uuid: "order-uuid-42", state: "draft" };
        await popup.finalizeOrder(order);

        expect(order.state).toBe("paid");
        expect(pendingOrderIds).toEqual([42]);
        expect(unsyncedSet.has("order-uuid-42")).toBe(true);
        expect(syncOptions).toEqual({ throw: false });
    });

    test("confirm finalizes order, calls props.close, and adds PrintPopup to dialog", async () => {
        const store = await initPosEnv();
        const order = store.addNewOrder();
        order.state = "draft";

        let closeCalled = false;
        let openedDialogComponent = null;
        let openedDialogProps = null;

        const popup = await mountWithCleanup(ConfirmationPopup, {
            props: {
                close: () => {
                    closeCalled = true;
                },
            },
        });

        // Intercept dialog.add
        popup.dialog = {
            add: (component, props) => {
                openedDialogComponent = component;
                openedDialogProps = props;
            },
        };

        await popup.confirm();

        expect(order.state).toBe("paid");
        expect(closeCalled).toBe(true);
        expect(openedDialogComponent).toBe(PrintPopup);
        expect(openedDialogProps.orderToPrint).toBe(order);
        expect(openedDialogProps.confirmText).toBe("Print");
        expect(openedDialogProps.cancelText).toBe("Cancel");
    });

    test("getPayload returns null", async () => {
        await initPosEnv();
        const popup = await mountWithCleanup(ConfirmationPopup, {
            props: { close: () => {} },
        });

        const payload = await popup.getPayload();
        expect(payload).toBe(null);
    });

    test("cancel invokes props.close", async () => {
        await initPosEnv();
        let closeCalled = false;

        const popup = await mountWithCleanup(ConfirmationPopup, {
            props: {
                close: () => {
                    closeCalled = true;
                },
            },
        });

        popup.cancel();
        expect(closeCalled).toBe(true);
    });
});
