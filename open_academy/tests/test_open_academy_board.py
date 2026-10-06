# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestOpenAcademyBoard(TransactionCase):

    def test_sanitize_dashboard_arch(self):
        """ Test parsing/sanitizing of board view architecture """
        raw_arch = """
        <form string="Session Dashboard">
            <board style="1-2">
                <column>
                    <action name="144" string="Sessions" context="" domain=""/>
                    <action name="145" string="Courses" context="null" domain="null"/>
                </column>
            </board>
        </form>
        """
        sanitized = self.env['board.board']._sanitize_openacademy_dashboard_arch(raw_arch)
        self.assertIn('context="{}"', sanitized)
        self.assertIn('domain="[]"', sanitized)

    def test_get_view_custom_view_creation(self):
        """ Test that get_view for openacademy dashboard automatically creates a custom view for the user """
        dashboard_view = self.env.ref('open_academy.board_session_form', raise_if_not_found=False)
        if not dashboard_view:
            return  # Skip test if the dashboard view is not loaded in this environment

        # Unlink any existing custom view for this user to have clean state
        self.env['ir.ui.view.custom'].sudo().search([
            ('user_id', '=', self.env.uid),
            ('ref_id', '=', dashboard_view.id),
        ]).unlink()

        res = self.env['board.board'].get_view(view_id=dashboard_view.id, view_type='form')
        self.assertTrue(res.get('custom_view_id'))

        custom_view = self.env['ir.ui.view.custom'].browse(res['custom_view_id'])
        self.assertTrue(custom_view.exists())
        self.assertEqual(custom_view.user_id.id, self.env.uid)
        self.assertEqual(custom_view.ref_id.id, dashboard_view.id)
