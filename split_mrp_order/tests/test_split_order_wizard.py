# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies <https://www.cybrosys.com>.
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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestSplitOrderWizard(TransactionCase):

    def setUp(self):
        super(TestSplitOrderWizard, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Finished Product',
            'type': 'consu',
            'is_storable': True,
        })
        self.component = self.env['product.product'].create({
            'name': 'Component',
            'type': 'consu',
        })
        self.workcenter = self.env['mrp.workcenter'].create({
            'name': 'Test Workcenter',
        })
        self.mo = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'product_qty': 10,
        })

    def test_01_split_by_quantity(self):
        """Test splitting by a specific quantity."""
        wizard = self.env['split.order'].create({
            'splitting_method': 'by_no_of_quantity',
            'no_of_quantity': 4,
            'order_id': self.mo.id,
            'work_center_id': self.workcenter.id,
        })
        wizard.action_split_done()
        
        # Original MO should now be 6
        self.assertEqual(self.mo.product_qty, 6)
        
        # New MO should be 4
        new_mo = self.env['mrp.production'].search([
            ('product_id', '=', self.product.id),
            ('id', '!=', self.mo.id)
        ], limit=1)
        self.assertTrue(new_mo)
        self.assertEqual(new_mo.product_qty, 4)

    def test_02_split_by_no_of_split(self):
        """Test splitting into multiple parts."""
        wizard = self.env['split.order'].create({
            'splitting_method': 'by_no_of_split',
            'no_of_split': 2,
            'order_id': self.mo.id,
            'work_center_id': self.workcenter.id,
        })
        # So it creates 5 MOs of qty 2. Actually the naming 'no_of_split' 
        # seems to mean 'split size' in this implementation logic.
        
        wizard.action_split_done()
        
        # Original MO should be deleted if reminder is 0
        self.assertFalse(self.mo.exists())
        
        new_mos = self.env['mrp.production'].search([
            ('product_id', '=', self.product.id)
        ])
        self.assertEqual(len(new_mos), 5)
        for m in new_mos:
            self.assertEqual(m.product_qty, 2)

    def test_03_split_manually(self):
        """Test manual split with a comma-separated string."""
        wizard = self.env['split.order'].create({
            'splitting_method': 'split_manually',
            'split_manually': '3,3,4',
            'order_id': self.mo.id,
            'work_center_id': self.workcenter.id,
        })
        wizard.action_split_done()
        
        # Original MO should be unlinked or updated depending on logic
        # For manual split, it unlinks the order if components are present, 
        # or updates the first and creates the rest if not.
        
        new_mos = self.env['mrp.production'].search([
            ('product_id', '=', self.product.id)
        ])
        self.assertEqual(len(new_mos), 3)
        self.assertEqual(sum(new_mos.mapped('product_qty')), 10)

    def test_04_split_manually_invalid_total(self):
        """Test manual split with total != qty."""
        wizard = self.env['split.order'].create({
            'splitting_method': 'split_manually',
            'split_manually': '3,3', # total 6 != 10
            'order_id': self.mo.id,
            'work_center_id': self.workcenter.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_split_done()
