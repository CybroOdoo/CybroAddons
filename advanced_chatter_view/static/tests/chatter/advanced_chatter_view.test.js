import {
    click,
    contains,
    defineMailModels,
    openFormView,
    start,
    startServer,
} from "@mail/../tests/mail_test_helpers";
import { describe, test } from "@odoo/hoot";

describe.current.tags("desktop");
defineMailModels();

test("advanced chatter view toggles: message, note, activity, and close", async () => {
    const pyEnv = await startServer();
    const partnerId = pyEnv["res.partner"].create({ name: "Test Chatter Partner" });
    await start();
    await openFormView("res.partner", partnerId);

    // Initial state: action buttons visible and chatter collapsed
    await contains(".o_adv_chatter_actions #send_message");
    await contains(".o_adv_chatter_actions #log_note");
    await contains(".o_adv_chatter_actions #active");
    await contains(".o-adv-chatter-collapsed");

    // Toggle Send Message
    await click(".o_adv_chatter_actions #send_message");
    await contains(".o-adv-chatter-expanded.o-adv-filter-message");
    await contains(".o_adv_chatter_close_btn");

    // Close chatter
    await click(".o_adv_chatter_close_btn");
    await contains(".o-adv-chatter-collapsed");
    await contains(".o_adv_chatter_actions #send_message");

    // Toggle Log Note
    await click(".o_adv_chatter_actions #log_note");
    await contains(".o-adv-chatter-expanded.o-adv-filter-note");
    await contains(".o_adv_chatter_close_btn");

    // Close chatter
    await click(".o_adv_chatter_close_btn");
    await contains(".o-adv-chatter-collapsed");

    // Toggle Activities
    await click(".o_adv_chatter_actions #active");
    await contains(".o-adv-chatter-expanded.o-adv-filter-activity");
    await contains(".o_adv_chatter_close_btn");

    // Close chatter back to collapsed
    await click(".o_adv_chatter_close_btn");
    await contains(".o-adv-chatter-collapsed");
    await contains(".o_adv_chatter_actions #send_message");
});
