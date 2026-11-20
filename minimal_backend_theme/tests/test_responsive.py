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

RESPONSIVE_HELPERS = JS_HELPERS + r"""
    const noPageOverflow = () => document.documentElement.scrollWidth <= window.innerWidth;
"""

# Phones: the search is a full-screen sheet with a Cancel button, the page
# never scrolls sideways, and the sidebar layout gives way to Odoo's own
# mobile menu.
PHONE_JS = r"""
(async () => {
""" + RESPONSIVE_HELPERS + r"""
    try {
        await sleep(1500);
        assert(noPageOverflow(), "page fits the phone width");
        assert(!q(".o_minimal_sidebar") || q(".o_minimal_sidebar").getClientRects().length === 0, "no sidebar on phones");
        (await waitFor(() => q(".o_minimal_search_trigger"), "search button")).click();
        const sheet = await waitFor(() => q(".o_minimal_menu_search"), "search sheet");
        await sleep(300);
        const rect = sheet.getBoundingClientRect();
        assert(rect.left === 0 && rect.top === 0, `sheet starts at the screen corner, got ${rect.left},${rect.top}`);
        assert(Math.round(rect.width) === window.innerWidth && Math.round(rect.height) === window.innerHeight,
            `sheet covers the screen, got ${rect.width}x${rect.height}`);
        assert(noPageOverflow(), "sheet fits the phone width");
        q(".o_minimal_ms_close").click();
        await waitFor(() => !q(".o_minimal_menu_search"), "Cancel closes the sheet");
        console.log("test successful");
    } catch (e) {
        console.error(e.message);
    }
})();
"""

# Tablets: the sidebar rests as the slim rail and opens over the page as a
# drawer - the page keeps its width - closed by the backdrop, Escape, or
# picking a menu.
TABLET_JS = r"""
(async () => {
""" + RESPONSIVE_HELPERS + r"""
    try {
        await sleep(1500);
        assert(noPageOverflow(), "page fits the tablet width");
        const sidebar = await waitFor(() => q(".o_minimal_sidebar"), "sidebar");
        const content = q(".o_action_manager");
        assert(sidebar.classList.contains("o_collapsed"), "sidebar starts as the rail");
        await sleep(300);
        const railRight = sidebar.getBoundingClientRect().right;
        assert(railRight < 80, `rail is slim, got ${railRight}px`);
        const contentLeft = content.getBoundingClientRect().left;
        assert(Math.abs(contentLeft - railRight) <= 1, "page starts after the rail");

        const openDrawer = async () => {
            q(".o_minimal_sidebar_toggle").click();
            await waitFor(() => q(".o_minimal_sidebar.o_drawer_open") && q(".o_minimal_sidebar_backdrop"), "drawer open");
            await sleep(300);
        };
        await openDrawer();
        assert(q(".o_minimal_sidebar").getBoundingClientRect().width > 200, "drawer shows the menus");
        assert(Math.abs(content.getBoundingClientRect().left - contentLeft) <= 1, "drawer covers the page, not squeezing it");

        q(".o_minimal_sidebar_backdrop").click();
        await waitFor(() => !q(".o_minimal_sidebar.o_drawer_open") && !q(".o_minimal_sidebar_backdrop"), "backdrop closes the drawer");

        await openDrawer();
        document.body.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
        await waitFor(() => !q(".o_minimal_sidebar.o_drawer_open"), "Escape closes the drawer");

        await openDrawer();
        [...document.querySelectorAll(".o_minimal_sidebar_item")].find((a) => a.textContent.trim() === "Fed. States").click();
        await waitFor(() => !q(".o_minimal_sidebar.o_drawer_open"), "picking a menu closes the drawer");
        await waitFor(() => q(".o_breadcrumb")?.textContent.includes("Fed. States"), "menu opened");
        console.log("test successful");
    } catch (e) {
        console.error(e.message);
    }
})();
"""


@tagged('post_install', '-at_install')
class TestResponsive(ThemeHttpCase):

    def setUp(self):
        super().setUp()
        self.set_option('menu_layout', 'vertical')

    def test_phone(self):
        self.browser_size = '390x844'
        self.browser_js('/odoo/action-base.action_country', PHONE_JS, login='admin', timeout=60)

    def test_tablet_sidebar_drawer(self):
        self.require_module('contacts', "needs the Contacts app")
        self.browser_size = '820x1180'
        self.browser_js('/odoo/action-base.action_country', TABLET_JS, login='admin', timeout=60)
