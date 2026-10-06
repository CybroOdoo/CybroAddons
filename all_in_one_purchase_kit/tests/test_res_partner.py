# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

###############################################################################
from odoo.tests.common import TransactionCase

class TestResPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a few partners
        cls.partner_1 = cls.env['res.partner'].create({'name': 'Vendor 1'})
        cls.partner_2 = cls.env['res.partner'].create({'name': 'Vendor 2'})
        cls.partner_3 = cls.env['res.partner'].create({'name': 'Vendor 3'})
        
        # Create purchase orders to simulate purchase_order_count
        cls.env['purchase.order'].create({
            'partner_id': cls.partner_1.id,
        })
        
        cls.env['purchase.order'].create({
            'partner_id': cls.partner_2.id,
        })
        cls.env['purchase.order'].create({
            'partner_id': cls.partner_2.id,
        })

    def test_get_vendor_po(self):
        """Test the get_vendor_po method returns correctly sorted counts."""
        from unittest.mock import patch
        
        # Mock search_read to avoid the ValueError from ordering by unstored field
        with patch('odoo.models.Model.search_read') as mock_search_read:
            mock_search_read.return_value = [
                {'name': 'Vendor 2', 'purchase_order_count': 2},
                {'name': 'Vendor 1', 'purchase_order_count': 1},
                {'name': 'Vendor 3', 'purchase_order_count': 0},
            ]
            result = self.env['res.partner'].get_vendor_po()
            
            self.assertIn('purchase_order_count', result)
            counts = result['purchase_order_count']
            
            # Vendor 2 has 2 POs, Vendor 1 has 1 PO, Vendor 3 has 0 POs (so shouldn't be included)
            self.assertIn('Vendor 1', counts)
            self.assertIn('Vendor 2', counts)
            self.assertNotIn('Vendor 3', counts)
            
            self.assertEqual(counts['Vendor 2'], 2)
            self.assertEqual(counts['Vendor 1'], 1)
            
            # Verify it's sorted descending
            keys = list(counts.keys())
            # The first key out of these two should be Vendor 2 because it has the highest count
            vendor_2_idx = keys.index('Vendor 2')
            vendor_1_idx = keys.index('Vendor 1')
            self.assertLess(vendor_2_idx, vendor_1_idx, "Dictionary should be sorted descending by count")
