# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):
    """Test cases for the ResPartner model."""
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Copy',
            'prestashop': 12345,
        })

    def test_copy_resets_prestashop(self):
        """Test that copying a partner resets the prestashop id."""
        copied_partner = self.partner.copy()
        self.assertFalse(copied_partner.prestashop)
        self.assertEqual(copied_partner.name, 'Test Partner Copy (copy)')
