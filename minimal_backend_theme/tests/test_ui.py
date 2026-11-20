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
from odoo.tests import new_test_user, tagged

from .common import JS_HELPERS, ThemeHttpCase

# Drives the real web client: the top bar search opens the menu search
# dialog, a query finds a nested menu with its path, Enter opens it, and the
# quick settings layout switches toggle their <body> class.
UI_CHECK_JS = r"""
(async () => {
""" + JS_HELPERS + r"""    try {
        window.__step = "open-click";
        const trig = await wait(".o_minimal_search_trigger");
        // Let the web client finish starting before interacting.
        await new Promise((r) => setTimeout(r, 1000));
        trig.click();

        const input = await wait(".o_minimal_menu_search input");
        assert(document.querySelector(".o_minimal_app_grid .o_minimal_app_tile"), "app grid shown on empty search");

        window.__step = "type";
        input.value = "configuration countries";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        await wait('.o_minimal_section_title[data-section="menus"]');
        const first = await wait(".o_minimal_result.active");
        const name = first.querySelector(".o_minimal_result_name").textContent.trim();
        const path = first.querySelector(".o_minimal_result_path").textContent.trim();
        assert(name === "Countries", `first result is Countries, got ${name}`);
        assert(path.includes("Configuration"), `path shows parents, got ${path}`);
        assert(first.querySelector("mark"), "matched words are highlighted");

        input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
        const start = Date.now();
        while (document.querySelector(".o_minimal_menu_search") && Date.now() - start < 5000) {
            await new Promise((r) => setTimeout(r, 50));
        }
        assert(!document.querySelector(".o_minimal_menu_search"), "dialog closed after Enter");
        const crumb = await wait(".o_breadcrumb .active, .o_last_breadcrumb_item");
        assert(crumb.textContent.includes("Countries"), `Countries action opened, got ${crumb.textContent}`);

        window.__step = "recent";
        // Recently opened menu is offered on the next empty search.
        (await wait(".o_minimal_search_trigger")).click();
        const recent = await wait(".o_minimal_result .o_minimal_result_name");
        assert(recent.textContent.trim() === "Countries", "recent menu listed");
        document.querySelector(".o_minimal_menu_search input").dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
        );

        window.__step = "shortcut";
        // Keyboard shortcut opens the dialog from anywhere.
        await new Promise((r) => setTimeout(r, 300));
        assert(!document.querySelector(".o_minimal_menu_search"), "dialog closed by Escape");
        document.body.dispatchEvent(
            new KeyboardEvent("keydown", { key: "F", code: "KeyF", ctrlKey: true, shiftKey: true, bubbles: true })
        );
        await wait(".o_minimal_menu_search input");
        document.querySelector(".o_minimal_menu_search input").dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
        );

        window.__step = "quick";
        // Quick settings: compact switch toggles the body class.
        await new Promise((r) => setTimeout(r, 300));
        (await wait(".o_minimal_qs_toggle")).click();
        const switches = await wait(".o_minimal_qs_menu");
        const compact = [...switches.querySelectorAll(".o_minimal_qs_switch")].find((el) =>
            el.textContent.includes("Compact view")
        );
        assert(compact, "compact switch present");
        compact.click();
        await new Promise((r) => setTimeout(r, 100));
        assert(document.body.classList.contains("o_minimal_compact"), "compact class applied");
        assert(document.querySelector(".o_minimal_qs_menu"), "menu stays open after switching");

        assert(document.querySelector(".o_minimal_qs_menu input:checked"), "switch shows checked state");
        // Menu layout: switch to the sidebar, navigate from it, switch back.
        window.__step = "layout";
        const visible = (el) => Boolean(el) && el.getClientRects().length > 0;
        assert(visible(document.querySelector(".o_menu_sections")), "top bar sections shown by default");
        assert(!visible(document.querySelector(".o_minimal_sidebar")), "sidebar hidden by default");
        document.querySelector('.o_minimal_segment[data-layout="vertical"]').click();
        // The content slides beside the sidebar in .2s.
        await new Promise((r) => setTimeout(r, 400));
        assert(document.body.classList.contains("o_minimal_menu_vertical"), "vertical class applied");
        assert(document.querySelector('.o_minimal_segment[data-layout="vertical"]').classList.contains("active"), "sidebar segment active");
        const sidebar = document.querySelector(".o_minimal_sidebar");
        assert(visible(sidebar), "sidebar visible in vertical layout");
        assert(!visible(document.querySelector(".o_menu_sections")), "top bar sections hidden in vertical layout");
        const actionManager = document.querySelector(".o_action_manager");
        assert(actionManager.getBoundingClientRect().left >= sidebar.getBoundingClientRect().right - 1, "content starts right of the sidebar");

        // Collapse to a slim rail and expand back (transitions take .2s).
        window.__step = "sidebar collapse";
        const expandedWidth = sidebar.getBoundingClientRect().width;
        document.querySelector(".o_minimal_sidebar_toggle").click();
        await new Promise((r) => setTimeout(r, 400));
        const rail = document.querySelector(".o_minimal_sidebar");
        assert(rail.classList.contains("o_collapsed"), "sidebar collapsed");
        assert(rail.getBoundingClientRect().width < 80 && expandedWidth > 200, `rail is slim, got ${rail.getBoundingClientRect().width}px (was ${expandedWidth}px)`);
        assert(!rail.querySelector(".o_minimal_sidebar_item"), "menus hidden in the rail");
        assert(rail.querySelector(".o_minimal_sidebar_app_button"), "app icon shown in the rail");
        assert(Math.abs(actionManager.getBoundingClientRect().left - rail.getBoundingClientRect().right) <= 1, "content follows the rail");
        assert(localStorage.getItem("minimal_backend_theme.sidebar_collapsed") === "1", "collapsed state remembered");
        rail.querySelector(".o_minimal_sidebar_app_button").click();
        await new Promise((r) => setTimeout(r, 400));
        assert(!document.querySelector(".o_minimal_sidebar.o_collapsed"), "app icon expands the sidebar");
        assert(document.querySelector(".o_minimal_sidebar .o_minimal_sidebar_item"), "menus back");
        assert(localStorage.getItem("minimal_backend_theme.sidebar_collapsed") === "0", "expanded state remembered");
        window.__step = "layout";
        document.body.click();
        await new Promise((r) => setTimeout(r, 200));
        const tags = [...document.querySelector(".o_minimal_sidebar").querySelectorAll(".o_minimal_sidebar_item")].find((a) => a.textContent.trim() === "Countries");
        assert(tags, "sidebar lists the current app's menus");
        tags.click();
        const activeItem = await wait(".o_minimal_sidebar_item.active");
        assert(activeItem.textContent.trim() === "Countries", `sidebar marks the open menu active, got ${activeItem.textContent}`);
        const group = sidebar.querySelector(".o_minimal_sidebar_group_toggle");
        group.click();
        await new Promise((r) => setTimeout(r, 100));
        // Dropdowns close on pointerdown, which .click() does not send: the
        // quick settings menu is still open here.
        if (!document.querySelector(".o_minimal_qs_menu")) {
            (await wait(".o_minimal_qs_toggle")).click();
        }
        (await wait('.o_minimal_segment[data-layout="horizontal"]')).click();
        await new Promise((r) => setTimeout(r, 100));
        assert(!document.body.classList.contains("o_minimal_menu_vertical"), "back to horizontal");
        assert(visible(document.querySelector(".o_menu_sections")), "top bar sections back");

        // The Settings page shows what Quick settings saved (compact on, top
        // bar layout): one shared set of options.
        window.__step = "settings in sync";
        if (!document.querySelector(".o_minimal_qs_menu")) {
            (await wait(".o_minimal_qs_toggle")).click();
        }
        await wait(".o_minimal_qs_menu");
        assert(document.querySelector(".o_minimal_qs_note").textContent.includes("all users"), "admin told options apply to all users");
        [...document.querySelectorAll(".o_minimal_qs_link")].find((el) => el.textContent.includes("Theme settings")).click();
        const compactSetting = await wait("#minimal_theme_compact input[type=checkbox]");
        assert(compactSetting.checked, "Settings show compact view on, as set from Quick settings");
        const layoutRadio = await wait("#minimal_theme_menu_layout input[type=radio][data-value=horizontal], #minimal_theme_menu_layout input[type=radio][value=horizontal]");
        assert(layoutRadio.checked, "Settings show the top bar layout, as set from Quick settings");

        // Full-screen app board: opened by the apps button, filters apps,
        // lists matching menus, opens the selected one with Enter.
        window.__step = "app board";
        (await wait(".o_navbar_apps_menu button")).click();
        const board = await wait(".o_minimal_app_board");
        // offsetWidth/Height: layout size, unaffected by the opening animation.
        assert(
            board.offsetWidth === document.documentElement.clientWidth && board.offsetHeight === window.innerHeight,
            `board covers the whole screen, got ${board.offsetWidth}x${board.offsetHeight}`
        );
        const tile = await wait(".o_minimal_app_board_grid .o_minimal_app_tile .o_minimal_app_tile_name");
        assert(tile.textContent.trim().length > 0, "app tiles show app names");
        assert(board.querySelector(".o_minimal_app_icon img, .o_minimal_app_icon_letter"), "app tiles show icons");
        const boardInput = board.querySelector("input");
        assert(document.activeElement === boardInput, "search field focused");
        boardInput.value = "cont";
        boardInput.dispatchEvent(new Event("input", { bubbles: true }));
        await new Promise((r) => setTimeout(r, 100));
        const names = [...board.querySelectorAll(".o_minimal_app_board_grid .o_minimal_app_tile_name")].map((el) => el.textContent.trim());
        assert(names.length === 1 && names[0] === "Contacts", `apps filtered, got ${names}`);
        assert(board.querySelector(".o_minimal_app_board_menus .o_minimal_result"), "matching menus listed");
        boardInput.value = "fed states";
        boardInput.dispatchEvent(new Event("input", { bubbles: true }));
        await new Promise((r) => setTimeout(r, 100));
        boardInput.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
        const boardStart = Date.now();
        while (document.querySelector(".o_minimal_app_board") && Date.now() - boardStart < 5000) {
            await new Promise((r) => setTimeout(r, 50));
        }
        assert(!document.querySelector(".o_minimal_app_board"), "board closed after Enter");
        const statesCrumb = await wait(".o_breadcrumb .active, .o_last_breadcrumb_item");
        assert(statesCrumb.textContent.includes("Fed. States"), `menu opened from the board, got ${statesCrumb.textContent}`);
        (await wait(".o_navbar_apps_menu button")).click();
        await wait(".o_minimal_app_board");
        document.querySelector(".o_minimal_app_board input").dispatchEvent(
            new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
        );
        // Closing re-renders while the menu opened above may still be loading.
        const escStart = Date.now();
        while (document.querySelector(".o_minimal_app_board") && Date.now() - escStart < 5000) {
            await new Promise((r) => setTimeout(r, 50));
        }
        assert(!document.querySelector(".o_minimal_app_board"), "Escape closes the board");
        console.log("test successful");
    } catch (e) {
        console.error(e.message);
    }
})();
"""


# Options are shared and only administrators change them: a regular user
# gets them applied, sees them read-only in Quick settings, and clicking
# changes nothing.
READONLY_CHECK_JS = r"""
(async () => {
""" + JS_HELPERS + r"""    try {
        await sleep(1500);
        const body = document.body.classList;
        if (!body.contains("o_minimal_menu_vertical")) throw new Error("vertical layout from Settings not applied");
        if (!body.contains("o_minimal_compact")) throw new Error("compact view from Settings not applied");
        q(".o_minimal_qs_toggle").click();
        await sleep(300);
        const menu = q(".o_minimal_qs_menu");
        if (!menu.querySelector(".o_minimal_qs_note").textContent.includes("administrator")) throw new Error("read-only note missing");
        if (![...menu.querySelectorAll(".o_minimal_segment")].every((b) => b.disabled)) throw new Error("layout buttons should be disabled");
        const compact = [...menu.querySelectorAll(".o_minimal_qs_switch")].find((el) => el.textContent.includes("Compact view"));
        if (!compact.querySelector("input").disabled) throw new Error("switches should be disabled");
        compact.click();
        await sleep(300);
        if (!body.contains("o_minimal_compact")) throw new Error("a regular user could change the shared option");
        if ([...menu.querySelectorAll(".o_minimal_qs_link")].some((el) => el.textContent.includes("Theme settings"))) {
            throw new Error("Theme settings link shown to a regular user");
        }
        console.log("test successful");
    } catch (e) {
        console.error(e.message);
    }
})();
"""


# The top bar search also finds records: typing a customer name lists it
# under its model, and opening it shows its form.
RECORD_SEARCH_JS = r"""
(async () => {
""" + JS_HELPERS + r"""    try {
        await sleep(1000);
        (await waitFor(() => q(".o_minimal_search_trigger"), "search field")).click();
        const input = await waitFor(() => q(".o_minimal_menu_search input"), "search dialog");
        input.value = "zephyr minimal";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        let record = await waitFor(
            () => [...document.querySelectorAll('.o_minimal_result[data-kind="record"]')]
                .find((el) => el.textContent.includes("Zephyr Minimal Corp")),
            "record result"
        );
        const header = q('.o_minimal_section_title[data-section="model_res.partner"]');
        if (!header || !header.textContent.includes("Contact")) throw new Error("records grouped under their type");

        // Scope tabs: Tab switches to Records only, a click to Menus only.
        const kinds = () => new Set([...document.querySelectorAll(".o_minimal_result")].map((el) => el.dataset.kind));
        input.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true }));
        await waitFor(() => q('.o_minimal_ms_scope.active[data-scope="menus"]'), "Tab moves to the Menus scope");
        input.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true }));
        await waitFor(() => q('.o_minimal_ms_scope.active[data-scope="records"]'), "Tab moves to the Records scope");
        if ([...kinds()].some((kind) => kind === "menu")) throw new Error("Records scope lists no menus");
        q('.o_minimal_ms_scope[data-scope="menus"]').click();
        await waitFor(() => ![...kinds()].includes("record"), "Menus scope lists no records");
        q('.o_minimal_ms_scope[data-scope="all"]').click();
        await waitFor(() => kinds().has("record"), "All scope lists records again");

        // Clear empties the field and goes back to recent menus and apps.
        q(".o_minimal_ms_clear").click();
        await waitFor(() => input.value === "" && q(".o_minimal_app_grid"), "search cleared");
        input.value = "zephyr minimal";
        input.dispatchEvent(new Event("input", { bubbles: true }));
        record = await waitFor(
            () => [...document.querySelectorAll('.o_minimal_result[data-kind="record"]')]
                .find((el) => el.textContent.includes("Zephyr Minimal Corp")),
            "record result again"
        );
        if (!(record.getAttribute("href") || "").match(/\/\d+$/)) throw new Error("record result links to the record");
        record.click();
        await waitFor(() => !q(".o_minimal_menu_search"), "dialog closed");
        await waitFor(
            () => q(".o_form_view") && q(".o_breadcrumb")?.textContent.includes("Zephyr Minimal Corp"),
            "record form opened"
        );
        console.log("test successful");
    } catch (e) {
        console.error(e.message);
    }
})();
"""


@tagged('post_install', '-at_install')
class TestMinimalBackendTheme(ThemeHttpCase):

    def test_menu_search_and_quick_settings(self):
        # Walks real menus of the Contacts app (Countries...).
        self.require_module('contacts', "needs the Contacts app")
        self.browser_js('/odoo', UI_CHECK_JS, login='admin', timeout=60)
        # Saved on the server, for everyone.
        ICP = self.env['ir.config_parameter'].sudo()
        self.assertTrue(ICP.get_bool('minimal_backend_theme.compact'))
        self.assertEqual(ICP.get_str('minimal_backend_theme.menu_layout'), 'horizontal')

    def test_regular_users_see_options_read_only(self):
        self.require_module('contacts', "needs the Contacts app")
        self.set_option('menu_layout', 'vertical')
        self.set_option('compact', True)
        new_test_user(self.env, login='theme_regular_user', groups='base.group_user')
        self.browser_js('/odoo/contacts', READONLY_CHECK_JS, login='theme_regular_user', timeout=60)
        self.assertTrue(self.env['ir.config_parameter'].sudo().get_bool('minimal_backend_theme.compact'))

    def test_record_search(self):
        self.env['res.partner'].create({'name': 'Zephyr Minimal Corp'})
        self.browser_js('/odoo', RECORD_SEARCH_JS, login='admin', timeout=60)
