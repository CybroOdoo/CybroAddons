# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestContractWasteSelection(TransactionCase):
    """Unit tests verifying contracted waste category selection and rate card lookups."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Contract Waste Customer'})

        cls.cat_plastic = cls.env['wm.waste.category'].create({'name': 'Plastic Category'})
        cls.cat_metal = cls.env['wm.waste.category'].create({'name': 'Metal Category'})

        cls.product_plastic_bottle = cls.env['product.product'].create({
            'name': 'Plastic Bottle',
            'is_waste_material': True,
            'wm_waste_category_id': cls.cat_plastic.id,
            'list_price': 5.0,
        })
        cls.product_plastic_bag = cls.env['product.product'].create({
            'name': 'Plastic Bag',
            'is_waste_material': True,
            'wm_waste_category_id': cls.cat_plastic.id,
            'list_price': 2.0,
        })
        cls.product_scrap_iron = cls.env['product.product'].create({
            'name': 'Scrap Iron',
            'is_waste_material': True,
            'wm_waste_category_id': cls.cat_metal.id,
            'list_price': 15.0,
        })

        cls.collection_point = cls.env['wm.collection.point'].create({
            'name': 'Contract Point',
            'partner_id': cls.partner.id,
        })

        cls.sla = cls.env['wm.sla'].create({
            'name': 'Standard SLA Waste Selection',
            'terms_and_conditions': 'Standard SLA terms and conditions',
        })

        cls.contract = cls.env['wm.partner.contract'].create({
            'name': 'WM-CONTRACT-TEST-001',
            'partner_id': cls.partner.id,
            'sla_id': cls.sla.id,
            'from_date': date.today(),
            'to_date': date.today() + timedelta(days=365),
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 500.0,
            'overweight_price': 10.0,
            'state': 'ongoing',
            'contract_line_ids': [(0, 0, {
                'category_id': cls.cat_plastic.id,
                'product_ids': [(6, 0, [cls.product_plastic_bottle.id])],
            })],
        })

    def test_order_with_contract_filters_waste_materials(self):
        """
        Order linked to contract filters contract_product_ids to specifically
        listed products.
        """
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'contract_id': self.contract.id,
        })
        # Specifically listed product_ids is included
        self.assertIn(self.product_plastic_bottle, order.contract_product_ids)
        # Unlisted product in same category is excluded since product_ids was explicitly specified
        self.assertNotIn(self.product_plastic_bag, order.contract_product_ids)
        # Product in different category is excluded
        self.assertNotIn(self.product_scrap_iron, order.contract_product_ids)

    def test_order_with_category_only_contract_line(self):
        """
        Contract line with category_id but no specific product_ids includes all
        products under that category.
        """
        partner_cat = self.env['res.partner'].create({
            'name': 'Category Contract Partner Test',
        })
        point_cat = self.env['wm.collection.point'].create({
            'name': 'Site Cat Test',
            'partner_id': partner_cat.id,
        })
        category_contract = self.env['wm.partner.contract'].create({
            'name': 'WM-CONTRACT-CATEGORY-ONLY',
            'partner_id': partner_cat.id,
            'sla_id': self.sla.id,
            'from_date': date.today(),
            'to_date': date.today() + timedelta(days=365),
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'category_rate',
            'state': 'ongoing',
            'contract_line_ids': [(0, 0, {
                'category_id': self.cat_plastic.id,
                'price': 2.50,
                'product_ids': [(6, 0, [])],
            })],
        })
        order = self.env['wm.collection.order'].create({
            'partner_id': partner_cat.id,
            'collection_point_id': point_cat.id,
            'contract_id': category_contract.id,
        })
        # All products under Plastic category are included
        self.assertIn(self.product_plastic_bottle, order.contract_product_ids)
        self.assertIn(self.product_plastic_bag, order.contract_product_ids)
        # Metal category product is excluded
        self.assertNotIn(self.product_scrap_iron, order.contract_product_ids)

    def test_order_without_contract_allows_any_waste(self):
        """
        Order without contract has False contract_product_ids, allowing any
        waste material.
        """
        partner_no_contract = self.env['res.partner'].create({
            'name': 'Partner Without Contract Test',
        })
        point_no_contract = self.env['wm.collection.point'].create({
            'name': 'Site No Contract',
            'partner_id': partner_no_contract.id,
        })
        order = self.env['wm.collection.order'].create({
            'partner_id': partner_no_contract.id,
            'collection_point_id': point_no_contract.id,
        })
        self.assertFalse(order.contract_id)
        self.assertFalse(order.contract_product_ids)

    def test_create_material_contract_without_price_succeeds(self):
        """
        Material-based billing contracts can be created with category lines
        where Rate per kg is not specified (defaults to 0.0), matching UI behavior.
        """
        contract = self.env['wm.partner.contract'].create({
            'name': 'WM-CONTRACT-MAT-NO-PRICE',
            'partner_id': self.partner.id,
            'sla_id': self.sla.id,
            'from_date': date.today(),
            'to_date': date.today() + timedelta(days=30),
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'material',
            'contract_line_ids': [(0, 0, {
                'category_id': self.cat_plastic.id,
                'product_ids': [(6, 0, [self.product_plastic_bottle.id])],
            })],
        })
        self.assertTrue(contract.id)
        self.assertEqual(contract.contract_line_ids[0].price, 0.0)

    def test_create_category_rate_contract_zero_price_fails(self):
        """
        Category-rate billing contracts strictly require a positive Rate per kg.
        """
        with self.assertRaises(ValidationError):
            self.env['wm.partner.contract'].create({
                'name': 'WM-CONTRACT-CR-ZERO-PRICE',
                'partner_id': self.partner.id,
                'sla_id': self.sla.id,
                'from_date': date.today(),
                'to_date': date.today() + timedelta(days=30),
                'frequency': 'weekly',
                'no_of_frequency': 1,
                'billing_basis': 'category_rate',
                'contract_line_ids': [(0, 0, {
                    'category_id': self.cat_plastic.id,
                    'price': 0.0,
                })],
            })
