# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
from odoo.tests import TransactionCase, tagged

@tagged('-at_install', 'post_install')
class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrder, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })

    def test_quotation_ref_creation(self):
        """Test that quotation_ref is assigned correctly when creating a sale order."""
        # Create a sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        
        # Check if quotation_ref is set
        self.assertTrue(sale_order.quotation_ref, "Quotation reference should be set upon creation.")
        self.assertTrue(sale_order.quotation_ref.startswith('SQ'), "Quotation reference should start with 'SQ'.")

    def test_multiple_quotation_ref_creation(self):
        """Test that quotation_ref is assigned correctly when creating multiple sale orders."""
        # Create multiple sale orders
        sale_orders = self.env['sale.order'].create([{
            'partner_id': self.partner.id,
        }, {
            'partner_id': self.partner.id,
        }])
        
        # Check if quotation_refs are unique and set correctly
        refs = [order.quotation_ref for order in sale_orders]
        self.assertEqual(len(refs), 2, "There should be two quotation references.")
        self.assertTrue(all(ref.startswith('SQ') for ref in refs), "All quotation references should start with 'SQ'.")
        self.assertNotEqual(refs[0], refs[1], "Quotation references should be unique.")
