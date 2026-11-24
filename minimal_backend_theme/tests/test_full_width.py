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

# On a wide screen, a form with a chatter shows it beside the form; the
# "Full-width forms" switch moves it below, so the form takes the whole
# width, and switching back restores it - without reloading the page.
FULL_WIDTH_JS = r"""
(async () => {
""" + JS_HELPERS + r"""    const toggleFullWidth = async () => {
        if (!q(".o_minimal_qs_menu")) {
            q(".o_minimal_qs_toggle").click();
            await waitFor(() => q(".o_minimal_qs_menu"), "quick settings");
        }
        [...document.querySelectorAll(".o_minimal_qs_switch")]
            .find((el) => el.textContent.includes("Full-width"))
            .click();
    };
    try {
        await waitFor(() => q(".o_form_sheet_bg") && q(".o-mail-Form-chatter"), "form with chatter");
        await sleep(500);
        if (!q(".o-mail-Form-chatter.o-aside")) throw new Error("chatter should start beside the form");
        const before = q(".o_form_sheet_bg").getBoundingClientRect().width;

        await toggleFullWidth();
        await waitFor(() => !q(".o-mail-Form-chatter.o-aside"), "chatter below the form");
        await sleep(300);
        const sheetBg = q(".o_form_sheet_bg").getBoundingClientRect();
        const chatter = q(".o-mail-Form-chatter").getBoundingClientRect();
        if (sheetBg.width < window.innerWidth * 0.95) throw new Error(`form not full width: ${sheetBg.width}px of ${window.innerWidth}px (was ${before}px)`);
        if (chatter.top < sheetBg.bottom - 1) throw new Error("chatter not below the form");

        await toggleFullWidth();
        await waitFor(() => q(".o-mail-Form-chatter.o-aside"), "chatter back beside the form");
        console.log("test successful");
    } catch (e) {
        console.error(e.message);
    }
})();
"""


@tagged('post_install', '-at_install')
class TestFullWidthForms(ThemeHttpCase):

    def test_full_width_moves_chatter_below(self):
        self.require_module('mail', "Discuss (mail) not installed: no chatter to move")
        self.browser_size = '1920x1080'
        partner = self.env['res.partner'].create({'name': 'Full Width Partner'})
        self.browser_js(
            f'/odoo/action-base.action_partner_form/{partner.id}',
            FULL_WIDTH_JS, login='admin', timeout=90,
        )
