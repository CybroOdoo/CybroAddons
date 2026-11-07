import { describe, expect, test } from "@odoo/hoot";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { onRpc, mountWithCleanup } from "@web/../tests/web_test_helpers";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { SaleOrderScreen } from "@click_and_collect_pos/js/click_and_collect_screen";

definePosModels();

describe("SaleOrderScreen", () => {
    test("SaleOrderScreen mounts and loads pending C&C order lines", async () => {
        const store = await setupPosEnv();

        onRpc("sale.order.line", "search_read", () => {
            return [{ id: 42 }];
        });

        onRpc("stock.picking", "action_stock_picking", () => {
            return [
                {
                    id: 42,
                    order_id: "S00001",
                    partner_id: "Test Customer",
                    product_id: "Desk Lamp",
                    product_uom_quantity: 2,
                },
            ];
        });

        const comp = await mountWithCleanup(SaleOrderScreen, { props: {} });
        expect(comp.state.loading).toBe(false);
        expect(comp.state.lines.length).toBe(1);
        expect(comp.state.lines[0].order_id).toBe("S00001");
        expect(comp.state.lines[0].product_id).toBe("Desk Lamp");
    });
});
