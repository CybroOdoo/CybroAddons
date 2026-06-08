# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPurchaseOrder(TransactionCase):
    """Test PurchaseOrder model functions from models/purchase_order.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.company = cls.env.user.company_id

    def test_default_notes_from_company(self):
        """Test _default_notes function correctly retrieves company purchase_terms."""
        expected_terms = "<p>Standard Company Purchase Terms</p>"
        self.company.purchase_terms = expected_terms
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(
            po.notes, expected_terms,
            "Purchase Order notes should default to the company's purchase_terms."
        )

    def test_default_notes_empty_when_not_set(self):
        """Test _default_notes when company purchase_terms is empty/False."""
        self.company.purchase_terms = False

        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })

        self.assertFalse(
            po.notes,
            "Purchase Order notes should be empty when company purchase_terms is not set."
        )
