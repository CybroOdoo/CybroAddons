# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import tagged

from .common import JS_HELPERS, ThemeHttpCase

# Pinned menus, recent records and "new ..." in the top bar search, and the
# pinned group of the sidebar.
PERSONAL_JS = r"""
(async () => {
""" + JS_HELPERS + r"""    const openSearch = async () => {
        q(".o_minimal_search_trigger").click();
        return waitFor(() => q(".o_minimal_menu_search input"), "search dialog");
    };
    const type = (input, text) => {
        input.value = text;
        input.dispatchEvent(new Event("input", { bubbles: true }));
    };
    const closeSearch = async () => {
        q(".o_minimal_menu_search input").dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        await waitFor(() => !q(".o_minimal_menu_search"), "search closed");
    };
    const section = (key) => q(`.o_minimal_section_title[data-section="${key}"]`);
    const rowsAfter = (key) => {
        const rows = [];
        let el = section(key)?.nextElementSibling;
        while (el && el.classList.contains("o_minimal_result")) {
            rows.push(el);
            el = el.nextElementSibling;
        }
        return rows;
    };
    try {
        await sleep(1500);

        // 1. Pin "Countries" from its search result.
        let input = await openSearch();
        type(input, "countries");
        const row = await waitFor(
            () => qa('.o_minimal_result[data-kind="menu"]').find((el) => el.querySelector(".o_minimal_result_name").textContent.trim() === "Countries"),
            "Countries result"
        );
        row.querySelector(".o_minimal_pin").click();
        await waitFor(() => row.querySelector(".o_minimal_pin.o_pinned"), "star filled");
        assert(q(".o_minimal_menu_search"), "pinning keeps the search open");
        type(input, "");
        await waitFor(() => section("pinned"), "Pinned section on the empty search");
        assert(rowsAfter("pinned").some((el) => el.textContent.includes("Countries")), "Countries listed as pinned");
        await closeSearch();

        // ... and in the sidebar, across apps.
        const pinnedGroup = await waitFor(() => q(".o_minimal_sidebar_pinned"), "sidebar pinned group");
        assert(pinnedGroup.textContent.includes("Countries"), "sidebar lists the pin");

        // 2. Open a record from the search: it becomes a recent record.
        input = await openSearch();
        type(input, "zephyr personal");
        (await waitFor(
            () => qa('.o_minimal_result[data-kind="record"]').find((el) => el.textContent.includes("Zephyr Personal Ltd")),
            "record result"
        )).click();
        await waitFor(() => q(".o_breadcrumb")?.textContent.includes("Zephyr Personal Ltd"), "record opened");
        input = await openSearch();
        await waitFor(() => section("recent_records"), "Recent records section");
        const recent = rowsAfter("recent_records")[0];
        assert(recent && recent.textContent.includes("Zephyr Personal Ltd"), "most recent record first");
        assert(recent.textContent.includes("Contact"), "recent record shows its type");

        // 3. "new country" creates a country, in its app.
        type(input, "new country");
        const create = await waitFor(() => q('.o_minimal_result[data-kind="create"]'), "Create result");
        assert(section("create"), "Create section shown");
        assert(create.textContent.includes("New Country"), `create row names the type, got ${create.textContent}`);
        assert((create.getAttribute("href") || "").endsWith("/new"), "create row links to a new record");
        assert(create.classList.contains("active"), "create row selected first");
        input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
        await waitFor(() => !q(".o_minimal_menu_search"), "search closed");
        await waitFor(() => q(".o_form_view .o_form_editable") && location.pathname.endsWith("/new"), "new record form");

        // Unpin from the sidebar.
        q(".o_form_button_cancel, .o_form_discard")?.click();
        await sleep(300);
        const sidebarPin = await waitFor(() => q(".o_minimal_sidebar_pinned .o_minimal_sidebar_pin.o_pinned"), "sidebar star");
        sidebarPin.click();
        await waitFor(() => !q(".o_minimal_sidebar_pinned"), "unpinned from the sidebar");
        console.log("test successful");
    } catch (e) {
        console.error(e.message);
    }
})();
"""


@tagged('post_install', '-at_install')
class TestPersonalUI(ThemeHttpCase):

    def test_pins_recent_records_and_create(self):
        self.require_module('contacts', "needs the Contacts app")
        self.set_option('menu_layout', 'vertical')
        self.browser_size = '1440x900'
        self.env['res.partner'].create({'name': 'Zephyr Personal Ltd'})
        self.browser_js('/odoo/action-base.action_country', PERSONAL_JS, login='admin', timeout=90)
        self.assertFalse(self.env['minimal_backend_theme.menu_pin'].search([]), "unpinned in the end")
