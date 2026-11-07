import { beforeEach, describe, expect, test } from "@odoo/hoot";
import { click, queryOne, tick } from "@odoo/hoot-dom";
import { mockService, onRpc, patchWithCleanup } from "@web/../tests/web_test_helpers";
import { setupInteractionWhiteList, startInteractions } from "@web/../tests/public/helpers";
import { PosDataPlugin } from "@point_of_sale/app/plugins/pos_data_plugin";
import { PosTicketPrinterPlugin } from "@point_of_sale/app/plugins/pos_ticket_printer_plugin";
import "@click_and_collect_pos/js/website_sale_cart";

beforeEach(() => {
    mockService("pos", () => ({}));
    patchWithCleanup(PosDataPlugin.prototype, {
        _onWillStart() {
            return false;
        },
    });
    patchWithCleanup(PosTicketPrinterPlugin.prototype, {
        initDefaultPrinter() {
            return false;
        },
        initPrinters() {
            return false;
        },
    });
});

setupInteractionWhiteList(["click_and_collect_pos.click_and_collect"]);
describe.current.tags("interaction_dev");

const CART_HTML = `
    <div class="oe_cart">
        <div class="click_and_collect_td">
            <input type="checkbox" name="click_and_collect"
                   id="is_click_and_collect_1"
                   class="form-check-input clickandecollect"
                   data-id="101" />
            <div class="text-center click_and_collect_td oe_session d-none">
                <select class="form-select session_values" name="pos_session" data-line-id="101">
                    <option value="select">Select Store</option>
                    <option value="5">Downtown POS Store</option>
                </select>
            </div>
        </div>
    </div>
`;

test("Toggling Click & Collect checkbox reveals store dropdown and sends RPC update", async () => {
    let rpcCalled = false;
    let rpcParams = null;

    onRpc("/shop/cart/update_click_and_collect", async (request) => {
        const { params } = await request.json();
        rpcCalled = true;
        rpcParams = params;
        return { status: "success" };
    });

    await startInteractions(CART_HTML);

    const checkbox = queryOne(".clickandecollect");
    const sessionDiv = queryOne(".oe_session");
    expect(sessionDiv.classList.contains("d-none")).toBe(true);

    // Click checkbox to enable C&C
    await click(checkbox);
    await tick();

    expect(sessionDiv.classList.contains("d-none")).toBe(false);
    expect(rpcCalled).toBe(true);
    expect(rpcParams.line_id).toBe(101);
    expect(rpcParams.is_click_and_collect).toBe(true);
});
