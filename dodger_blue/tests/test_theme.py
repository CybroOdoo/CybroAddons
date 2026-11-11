# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

"""Exercise the login view and searchable application navigation."""

from lxml import html

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestDodgerBlue(HttpCase):
    """Verify the theme through rendered pages and the actual web client."""

    def test_login_buttons(self):
        """The inherited login template keeps a working, styled submit button."""
        response = self.url_open("/web/login")
        self.assertEqual(response.status_code, 200)
        page = html.fromstring(response.content)
        buttons = page.xpath("//form//button[@type='submit'][not(@name)]")
        self.assertTrue(buttons)
        self.assertIn("cybro-login-btn", buttons[0].get("class", "").split())
        self.assertTrue(page.xpath("//input[@name='login']"))
        self.assertTrue(page.xpath("//input[@name='password']"))

    def test_sidebar_search(self):
        """Search, empty results, reset, and application navigation work in OWL."""
        self.browser_js(
            "/odoo",
            """
            (async () => {
                const waitFor = async (check) => {
                    for (let i = 0; i < 100; i++) {
                        if (check()) { return; }
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }
                    throw new Error("Theme UI did not reach the expected state");
                };
                const sidebar = document.querySelector('.cybro-sidebar-qweb');
                if (!sidebar || !sidebar.querySelector('a.o_app')) {
                    throw new Error("Application sidebar is missing");
                }
                document.querySelector('.cybro-sidebar-toggle').click();
                await waitFor(() => document.querySelector('.cybro-main-menu input'));
                const menu = document.querySelector('.cybro-main-menu');
                const input = menu.querySelector('input');
                const app = menu.querySelector('a.o_app');
                const label = app.textContent.trim();
                const search = value => {
                    input.value = value;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                };
                search('zzzz_no_such_application_12345');
                await waitFor(() => menu.textContent.includes('No menus found'));
                search(label);
                await waitFor(() => !menu.textContent.includes('No menus found') &&
                    menu.querySelector('.dropdown-item'));
                if (!menu.textContent.includes(label)) {
                    throw new Error("Search did not return the matching application");
                }
                search('   ');
                await waitFor(() => menu.querySelector('a.o_app'));
                search(label);
                await waitFor(() => menu.querySelector('.dropdown-item') &&
                    !menu.querySelector('a.o_app'));
                menu.querySelector('.dropdown-item').click();
                await waitFor(() => document.querySelector('.o_action_manager > *'));
                console.log('test successful');
            })();
            """,
            ready="odoo.isReady === true",
            login="admin",
            timeout=120,
        )

    def test_company_switcher_layout(self):
        """Company labels, checkboxes, and search fit without overlapping."""
        company = self.env["res.company"].create({"name": "Theme Layout Company"})
        self.env.ref("base.user_admin").company_ids |= company
        self.browser_js(
            "/odoo",
            """
            (async () => {
                document.querySelector('.o_switch_company_menu').click();
                let menu;
                for (let i = 0; i < 100; i++) {
                    menu = document.querySelector('.o_switch_company_menu_dropdown');
                    if (menu) { break; }
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                if (!menu) { throw new Error('Company switcher did not open'); }
                const toggleStyle = getComputedStyle(
                    document.querySelector('.o_switch_company_menu')
                );
                if (toggleStyle.backgroundColor !== 'rgb(62, 142, 247)' ||
                    toggleStyle.color !== 'rgb(255, 255, 255)') {
                    throw new Error('Open company selector must keep its blue background and white text');
                }
                const input = menu.querySelector('[role="searchbox"]');
                const search = menu.querySelector('[role="search"]');
                const inputRect = input.getBoundingClientRect();
                const searchRect = search.getBoundingClientRect();
                if (inputRect.height > 40 || inputRect.left < searchRect.left ||
                    inputRect.right > searchRect.right + 1) {
                    throw new Error('Company search bounds: ' + JSON.stringify({input:inputRect.toJSON(),search:searchRect.toJSON()}));
                }
                for (const item of menu.querySelectorAll('.o_switch_company_item')) {
                    const checkbox = item.querySelector('input').getBoundingClientRect();
                    const label = item.querySelector('.company_label').getBoundingClientRect();
                    if (checkbox.right > label.left || checkbox.height > 20 ||
                        checkbox.width > 20) {
                        throw new Error('Company checkbox overlap: ' + JSON.stringify({checkbox:checkbox.toJSON(),label:label.toJSON()}));
                    }
                }
                input.value = 'Theme Layout Company';
                input.dispatchEvent(new Event('input', { bubbles: true }));
                for (let i = 0; i < 100; i++) {
                    const items = menu.querySelectorAll('.o_switch_company_item');
                    if (items.length === 1 && items[0].textContent.includes(input.value)) {
                        console.log('test successful');
                        return;
                    }
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                throw new Error('Company search failed to filter entries');
            })();
            """,
            ready="odoo.isReady === true",
            login="admin",
            timeout=120,
        )

    def test_debug_user_menu_layout(self):
        """The debug name and database badge fit inside the navbar."""
        self.browser_js(
            "/odoo?debug=1",
            """
            (async () => {
                const button = document.querySelector('.o_user_menu');
                const header = document.querySelector('.o_main_navbar').getBoundingClientRect();
                for (const selector of ['.o_user_avatar', '.oe_topbar_name', 'mark']) {
                    const element = button.querySelector(selector);
                    const rect = element.getBoundingClientRect();
                    if (!rect.height || rect.top < header.top || rect.bottom > header.bottom) {
                        throw new Error('User menu overflow: ' + selector + JSON.stringify({rect:rect.toJSON(),header:header.toJSON(),button:button.getBoundingClientRect().toJSON()}));
                    }
                }
                button.click();
                for (let i = 0; i < 100; i++) {
                    const logout = document.querySelector('[data-menu="logout"]');
                    if (logout && i > 2) {
                        const style = getComputedStyle(button);
                        if (style.backgroundColor !== 'rgb(62, 142, 247)' ||
                            style.color !== 'rgb(255, 255, 255)') {
                            throw new Error('Open user menu button must stay blue with white text');
                        }
                        const dropdown = logout.closest('.o-dropdown--menu');
                        if (dropdown.getBoundingClientRect().top < header.bottom - 1) {
                            throw new Error('User dropdown overlaps the navbar: ' + JSON.stringify({header: header.toJSON(), menu: dropdown.getBoundingClientRect().toJSON()}));
                        }
                        console.log('test successful');
                        return;
                    }
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                throw new Error('User menu did not open');
            })();
            """,
            ready="odoo.isReady === true",
            login="admin",
            timeout=120,
        )

    def test_debug_icon_active_color(self):
        """The navbar icon stays visible with the dropdown active class."""
        self.browser_js(
            "/odoo?debug=1",
            """
            (async () => {
                const icon = document.querySelector('.o_debug_manager i');
                const button = icon.closest('button');
                for (const state of ['', 'show']) {
                    button.classList.toggle('show', !!state);
                    button.focus();
                    if (getComputedStyle(button).backgroundColor !== 'rgb(62, 142, 247)') {
                        throw new Error('Focused navbar button must keep the blue background');
                    }
                }
                button.classList.add('show');
                const wrapper = button.parentElement;
                wrapper.classList.add('show');
                const legacyIcon = document.createElement('i');
                legacyIcon.className = 'fa fa-clock-o';
                button.appendChild(legacyIcon);
                if (getComputedStyle(legacyIcon).color !== 'rgb(255, 255, 255)' ||
                    getComputedStyle(legacyIcon, '::before').color !== 'rgb(255, 255, 255)') {
                    throw new Error('Activity icon is blue on blue in an open wrapper');
                }
                for (let i = 0; i < 100; i++) {
                    if (button.classList.contains('show')) {
                        const foreground = getComputedStyle(icon).color;
                        const background = getComputedStyle(button).backgroundColor;
                        if (foreground !== 'rgb(255, 255, 255)' ||
                            background !== 'rgb(62, 142, 247)') {
                            throw new Error('Active navbar icon has incorrect contrast');
                        }
                        console.log('test successful');
                        return;
                    }
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
                throw new Error('Developer menu did not open');
            })();
            """,
            ready="odoo.isReady === true",
            login="admin",
            timeout=120,
        )
