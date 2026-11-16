/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useTrackedAsync } from "@point_of_sale/app/hooks/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Sends order data to server for direct kitchen printing via PrintNode
 * and displays success or failure notification in the POS UI.
 */
async function printKitchenOrder(pos, order) {
    if (!order || order.isEmpty()) {
        return;
    }

    try {
        const table = order.getTable?.();
        const tableName = table
            ? (table.getName?.() || table.table_number?.toString() || table.name || "")
            : "";

        const orderName = (order.pos_reference && order.pos_reference !== "/")
            ? order.pos_reference
            : (order.name && order.name !== "/"
                ? order.name
                : (order.tracking_number ? String(order.tracking_number) : order.getName?.())) || "Order";

        // Prepare data for server-side kitchen printing
        const orderData = {
            name: orderName,
            pos_config_id: pos.config.id,
            table_name: tableName,
            order_type: table ? "Dine In" : (order.preset_id?.name === "Takeout" ? "Take Out" : (order.preset_id?.name || "Take Out")),
            order_customer_note: order.general_customer_note || "",
            order_internal_note: order.internal_note || "",
            lines: order.lines.map((line) => ({
                product_id: line.product_id.id,
                full_product_name: line.getFullProductName?.() || line.product_id.display_name || line.product_id.name || "",
                qty: line.qty ?? line.getQuantity?.() ?? 0,
                customer_note: line.getCustomerNote?.() || "",
                internal_note: line.getNote?.() || "",
            })),
        };

        // Call server-side print logic
        const result = await pos.data.call(
            "pos.order",
            "print_kitchen_order",
            [orderData]
        );

        if (result && result.success) {
            pos.notification.add(
                result.message || _t("Kitchen order printed successfully."),
                {
                    type: result.partial ? "warning" : "success",
                }
            );
        } else if (result && !result.success) {
            pos.notification.add(
                result.message || _t("Failed to print kitchen order."),
                {
                    type: "danger",
                    sticky: true,
                }
            );
        }
    } catch (error) {
        pos.notification.add(
            _t("Kitchen printing error: %s", error?.data?.message || error?.message || error),
            {
                type: "danger",
                sticky: true,
            }
        );
    }
}

patch(ActionpadWidget.prototype, {
    setup() {
        super.setup(...arguments);
        this.doSubmitOrder = useTrackedAsync(async () => {
            const order = this.pos.getOrder();
            if (!order || order.isEmpty()) {
                return;
            }

            // Print to kitchen via PrintNode before navigation
            await printKitchenOrder(this.pos, order);

            // Standard POS Order Submission (transitions to floor plan in pos_restaurant)
            await this.pos.submitOrder();
        });

        this.doReprintOrder = useTrackedAsync(async () => {
            const order = this.pos.getOrder();
            if (!order || order.isEmpty()) {
                return;
            }

            await printKitchenOrder(this.pos, order);
            await this.pos.reprintOrder();
        });
    },
});

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.doSubmitOrder = useTrackedAsync(async () => {
            const order = this.pos.getOrder();
            if (!order || order.isEmpty()) {
                return;
            }

            await printKitchenOrder(this.pos, order);
            await this.pos.submitOrder();
        });

        this.doReprintOrder = useTrackedAsync(async () => {
            const order = this.pos.getOrder();
            if (!order || order.isEmpty()) {
                return;
            }

            await printKitchenOrder(this.pos, order);
            await this.pos.reprintOrder();
        });
    },
});
