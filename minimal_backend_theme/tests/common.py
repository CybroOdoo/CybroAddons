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
from odoo.tests import HttpCase

# Helpers shared by the browser checks (pasted at the top of each script).
JS_HELPERS = r"""
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const q = (selector) => document.querySelector(selector);
    const qa = (selector) => [...document.querySelectorAll(selector)];
    const assert = (cond, msg) => {
        if (!cond) {
            throw new Error(`Assertion failed: ${msg}`);
        }
    };
    const waitFor = async (check, what) => {
        for (let i = 0; i < 200; i++) {
            const found = check();
            if (found) {
                return found;
            }
            await sleep(50);
        }
        throw new Error(`Timed out waiting for: ${what}`);
    };
    const wait = (selector, root = document) =>
        waitFor(() => root.querySelector(selector), `${selector} (step: ${window.__step})`);
"""


class ThemeHttpCase(HttpCase):
    """Browser tests start from the theme's defaults whatever the database
    holds (all rolled back): options, and no pinned menus."""

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().search(
            [('key', '=like', 'minimal_backend_theme.%')],
        ).unlink()
        self.env['minimal_backend_theme.menu_pin'].search([]).unlink()

    def set_option(self, key, value):
        ICP = self.env['ir.config_parameter'].sudo()
        if isinstance(value, bool):
            ICP.set_bool(f'minimal_backend_theme.{key}', value)
        else:
            ICP.set_str(f'minimal_backend_theme.{key}', value)

    def require_module(self, name, reason):
        if self.env['ir.module.module']._get(name).state != 'installed':
            self.skipTest(reason)
