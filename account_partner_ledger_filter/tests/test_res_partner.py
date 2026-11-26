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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestResPartner(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Action'
        })

    def test_get_wizard(self):
        """Test if the get_wizard method returns the correct action dictionary."""
        partner_with_context = self.partner.with_context(active_ids=self.partner.ids)
        action = partner_with_context.get_wizard()

        self.assertTrue(isinstance(action, dict))
        self.assertEqual(action.get('context', {}).get('default_partner_ids'), self.partner.ids)
        self.assertTrue(action.get('context', {}).get('create'))

    def test_get_wizard_without_active_ids(self):
        """Calling the method on records also selects those partners."""
        action = self.partner.get_wizard()
        self.assertEqual(action['context']['default_partner_ids'], self.partner.ids)
