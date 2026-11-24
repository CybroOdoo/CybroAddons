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
import shutil

from odoo.tests import tagged

from .common import JS_HELPERS, ThemeHttpCase

# A right-to-left language mirrors the theme: sidebar on the right, panel
# icons and chevrons pointing the right way, arrow keys following the
# reading direction, key combinations still read left to right.
RTL_JS = r"""
(async () => {
""" + JS_HELPERS + r"""    try {
        await sleep(1500);
        assert(document.body.classList.contains("o_rtl"), "page in right-to-left mode");
        assert(document.documentElement.scrollWidth <= window.innerWidth, "no sideways scrolling");

        // Sidebar on the right, the page on its left.
        const sidebar = await waitFor(() => q(".o_minimal_sidebar"), "sidebar");
        await sleep(300);
        const side = sidebar.getBoundingClientRect();
        assert(Math.abs(side.right - window.innerWidth) <= 1, `sidebar against the right edge, got ${side.right}/${window.innerWidth}`);
        const content = q(".o_action_manager").getBoundingClientRect();
        assert(Math.abs(content.right - side.left) <= 1, "page ends where the sidebar starts");
        assert(q('.o_minimal_sidebar_group:not(.o_folded) .o_minimal_sidebar_chevron[data-icon="keyboard_arrow_down"]'), "open groups point down");

        // Layout switch: the sidebar icon shows the panel on the right.
        q(".o_minimal_qs_toggle").click();
        await waitFor(() => q(".o_minimal_qs_menu"), "quick settings");
        assert(q('.o_minimal_segment[data-layout="vertical"] .oi[data-icon="dock_to_right"]'), "sidebar icon mirrored");
        document.body.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));
        document.body.click();
        await sleep(200);

        // Key combinations keep their left-to-right order.
        const kbd = q(".o_minimal_search_trigger .o_minimal_kbd");
        assert(getComputedStyle(kbd).direction === "ltr", "shortcut chip reads left to right");

        // App board: the left arrow moves to the next tile.
        q(".o_navbar_apps_menu button").click();
        await waitFor(() => q(".o_minimal_app_board_grid .o_minimal_app_tile.active"), "app board");
        const tiles = [...document.querySelectorAll(".o_minimal_app_board_grid .o_minimal_app_tile")];
        assert(tiles[1].getBoundingClientRect().right <= tiles[0].getBoundingClientRect().left + 1, "tiles flow from right to left");
        q(".o_minimal_app_board input").dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true }));
        await waitFor(() => tiles[1].classList.contains("active"), "ArrowLeft selects the next tile");
        console.log("test successful");
    } catch (e) {
        console.error(e.message);
    } finally {
        // The browser is shared by the following tests: drop the web client's
        // caches (menus...), filled here in Arabic.
        for (const { name } of await indexedDB.databases()) {
            indexedDB.deleteDatabase(name);
        }
    }
})();
"""


@tagged('post_install', '-at_install')
class TestRightToLeft(ThemeHttpCase):

    def test_rtl_layout(self):
        # Odoo mirrors the styles with the rtlcss tool; without it the
        # server serves them unmirrored (and logs a warning).
        if not shutil.which('rtlcss'):
            self.skipTest("rtlcss is not installed (npm install -g rtlcss)")
        self.require_module('contacts', "needs the Contacts app")
        self.env['res.lang']._activate_lang('ar_001')
        self.env.ref('base.user_admin').lang = 'ar_001'
        self.set_option('menu_layout', 'vertical')
        self.browser_size = '1440x900'
        self.browser_js('/odoo/action-base.action_country', RTL_JS, login='admin', timeout=90)
