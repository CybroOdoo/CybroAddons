# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
from odoo.tests import common


class TestUomInPricelist(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestUomInPricelist, cls).setUpClass()

        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Get standard UoMs
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_dozen = cls.env.ref('uom.product_uom_dozen')

        # Create a test product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product UOM Pricelist',
            'list_price': 100.0,
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id,
        })

        # Create a test pricelist
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Pricelist UOM',
        })

        # Create a pricelist item
        cls.pricelist_item = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'compute_price': 'fixed',
            'fixed_price': 80.0,
        })

    def test_01_product_uom_id_compute(self):
        """ Test the compute method of product_uom_id on pricelist item. """
        # When creating without product_uom_id, it should compute it from the template
        self.assertEqual(
            self.pricelist_item.product_uom_id,
            self.product.product_tmpl_id.uom_id,
            "product_uom_id should be computed from product_tmpl_id.uom_id"
        )

        # Change the product_tmpl_id to trigger compute
        other_product = self.env['product.product'].create({
            'name': 'Other Product',
            'uom_id': self.uom_dozen.id,
        })
        self.pricelist_item.product_tmpl_id = other_product.product_tmpl_id.id
        self.assertEqual(
            self.pricelist_item.product_uom_id,
            other_product.product_tmpl_id.uom_id,
            "product_uom_id should re-compute when product_tmpl_id changes"
        )

    def test_02_is_applicable_for_uom(self):
        """ Test whether the pricelist rule applies correctly based on the UoM. """
        # Set a specific uom for the pricelist item manually
        self.pricelist_item.product_uom_id = self.uom_dozen.id

        # Check applicability for unit UoM (should be False because uom_dozen != uom_unit)
        is_applicable_unit = self.pricelist_item._is_applicable_for(
            self.product, 1.0, self.uom_unit)
        self.assertFalse(is_applicable_unit, "Rule should not be applicable for mismatching UoM")

        # Check applicability for dozen UoM (should be True)
        is_applicable_dozen = self.pricelist_item._is_applicable_for(
            self.product, 1.0, self.uom_dozen)
        self.assertTrue(is_applicable_dozen, "Rule should be applicable for matching UoM")

    def test_03_compute_price_rule_with_uom(self):
        """ Test the _compute_price_rule function of product_pricelist """
        # Update the rule to apply only to Dozens
        self.pricelist_item.product_uom_id = self.uom_dozen.id

        # Compute price for Unit - should not use the pricelist item
        rules_unit = self.pricelist._compute_price_rule(
            products=self.product,
            quantity=1,
            uom=self.uom_unit
        )
        price_unit, rule_id_unit = rules_unit.get(self.product.id)
        self.assertNotEqual(rule_id_unit, self.pricelist_item.id, "Rule should not be applied for Unit UoM")

        # Compute price for Dozen - should use the pricelist item
        rules_dozen = self.pricelist._compute_price_rule(
            products=self.product,
            quantity=1,
            uom=self.uom_dozen
        )
        price_dozen, rule_id_dozen = rules_dozen.get(self.product.id)
        self.assertEqual(rule_id_dozen, self.pricelist_item.id, "Rule should be applied for Dozen UoM")
