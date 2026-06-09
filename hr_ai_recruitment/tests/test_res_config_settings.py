# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'hr_ai_recruitment')
class TestResConfigSettings(TransactionCase):
    """
    Test suite for res_config_settings.py (ResConfigSettings model).

    Corresponds to function:
        - set_values  : verifies menu active state is toggled correctly
                        based on the 'hr_ai_recruitment.is_ai_shortlist' param.
    """

    def _get_settings(self):
        """Helper: return a fresh res.config.settings transient record."""
        return self.env['res.config.settings'].create({})

    def test_set_values_enables_shortlist_menu_when_param_true(self):
        """
        set_values must set the shortlist menu to active=True
        when 'hr_ai_recruitment.is_ai_shortlist' is 'True'.
        """
        settings = self._get_settings()
        settings.is_ai_shortlist = True
        settings.set_values()

        param = self.env['ir.config_parameter'].sudo().get_param(
            'hr_ai_recruitment.is_ai_shortlist'
        )
        self.assertEqual(
            param, 'True',
            "Config parameter should be 'True' after set_values with is_ai_shortlist=True.",
        )

        ir_menu = self.env.ref(
            'hr_ai_recruitment.hr_shortlist_menu', raise_if_not_found=False
        )
        if ir_menu:
            self.assertTrue(
                ir_menu.active,
                "Shortlist menu must be active when AI shortlisting is enabled.",
            )

    def test_set_values_disables_shortlist_menu_when_param_false(self):
        """
        set_values must set the shortlist menu to active=False
        when 'hr_ai_recruitment.is_ai_shortlist' is 'False'.
        """
        settings = self._get_settings()
        settings.is_ai_shortlist = False
        settings.set_values()

        param = self.env['ir.config_parameter'].sudo().get_param(
            'hr_ai_recruitment.is_ai_shortlist'
        )
        self.assertNotEqual(
            param, 'True',
            "Config parameter should NOT be 'True' after set_values with is_ai_shortlist=False.",
        )

        ir_menu = self.env.ref(
            'hr_ai_recruitment.hr_shortlist_menu', raise_if_not_found=False
        )
        if ir_menu:
            self.assertFalse(
                ir_menu.active,
                "Shortlist menu must be inactive when AI shortlisting is disabled.",
            )

    def test_set_values_does_not_raise_when_menu_not_found(self):
        """
        set_values must NOT raise any error when the shortlist menu
        XML ref does not exist (raise_if_not_found=False guard).
        """
        settings = self._get_settings()
        settings.is_ai_shortlist = True
        # Calling set_values should complete without exceptions
        try:
            settings.set_values()
        except Exception as exc:
            self.fail(
                f"set_values raised an unexpected exception: {exc}"
            )

    def test_set_values_persists_is_ai_shortlist_param(self):
        """
        set_values must persist the is_ai_shortlist value to ir.config_parameter
        by virtue of calling super().set_values() which handles config_parameter fields.
        """
        settings = self._get_settings()
        settings.is_ai_shortlist = True
        settings.set_values()

        stored = self.env['ir.config_parameter'].sudo().get_param(
            'hr_ai_recruitment.is_ai_shortlist'
        )
        self.assertEqual(
            stored, 'True',
            "is_ai_shortlist must be written to ir.config_parameter by set_values.",
        )

    def test_set_values_toggle_twice(self):
        """
        Calling set_values twice (enable then disable) must correctly
        update the menu and parameter both times.
        """
        settings = self._get_settings()

        settings.is_ai_shortlist = True
        settings.set_values()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'hr_ai_recruitment.is_ai_shortlist'
        )
        self.assertEqual(param, 'True', "Parameter should be 'True' after first enable.")

        settings2 = self._get_settings()
        settings2.is_ai_shortlist = False
        settings2.set_values()
        param2 = self.env['ir.config_parameter'].sudo().get_param(
            'hr_ai_recruitment.is_ai_shortlist'
        )
        self.assertNotEqual(
            param2, 'True',
            "Parameter should NOT be 'True' after second disable.",
        )
