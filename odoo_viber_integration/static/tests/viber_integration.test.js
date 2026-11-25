import { expect, test } from "@odoo/hoot";
import { queryAllTexts, waitFor } from "@odoo/hoot-dom";
import {
    contains,
    mountWithCleanup,
    onRpc,
} from "@web/../tests/web_test_helpers";
import { ViberSystray } from "@odoo_viber_integration/js/viber_integration";

test("loads contact names and phone values from the server", async () => {
    onRpc("/web/dataset/call_kw/res.users/get_users", () => ({
        users: [
            { id: 1, name: "Alice", phone: "+91 (123) 456-7890" },
            { id: 2, name: "Bob", phone: "+44 123456" },
        ],
    }));
    await mountWithCleanup(ViberSystray);
    await waitFor("#user_select option:nth-child(3)");
    expect(queryAllTexts("#user_select option")).toEqual([
        "Choose a user to contact...", "Alice", "Bob",
    ]);
    expect("#user_select").toHaveValue("");
    expect('#user_select option:nth-child(2)').toHaveAttribute("value", "+91 (123) 456-7890");
});

test("opens and closes the initially hidden contact form", async () => {
    onRpc("/web/dataset/call_kw/res.users/get_users", () => ({ users: [] }));
    await mountWithCleanup(ViberSystray);
    await waitFor("#user_select option");
    expect("#viber_msg_form").not.toBeVisible();
    await contains(".viber-systray").click();
    expect("#viber_msg_form").toBeVisible();
    await contains("#close_viber").click();
    expect("#viber_msg_form").not.toBeVisible();
});

test("an empty contact list keeps only the placeholder", async () => {
    onRpc("/web/dataset/call_kw/res.users/get_users", () => ({ users: [] }));
    await mountWithCleanup(ViberSystray);
    await waitFor("#user_select option");
    expect(queryAllTexts("#user_select option")).toEqual(["Choose a user to contact..."]);
});
