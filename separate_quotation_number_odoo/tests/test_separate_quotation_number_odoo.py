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
#############################################################################
from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestSeparateQuotationNumber(TransactionCase):
    """Test suite for the separate quotation number on sale orders,

    covering the sequence configuration, the reference generation on
    create, the duplication behaviour, the confirmation flow, the form and
    list views and access rights.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order_model = cls.env['sale.order']
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Quotation Partner',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Quotation Product',
            'list_price': 100.0,
        })
        cls.sequence = cls.env.ref(
            'separate_quotation_number_odoo.seq_quotation')

    @classmethod
    def _get_order_vals(cls, with_line=False):
        """Return the values needed to create a test quotation."""
        vals = {'partner_id': cls.partner.id}
        if with_line:
            vals['order_line'] = [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 1.0,
            })]
        return vals

    def test_01_sequence_configuration(self):
        """Verify the quotation sequence is created with its configuration."""
        self.assertEqual(self.sequence.name, 'Quotation')
        self.assertEqual(self.sequence.code, 'sale.order')
        self.assertEqual(self.sequence.prefix, 'SQ')
        self.assertEqual(self.sequence.padding, 5)
        self.assertFalse(self.sequence.company_id)

    def test_02_quotation_ref_generated_on_create(self):
        """Verify a new quotation receives a reference from the sequence."""
        order = self.sale_order_model.create(self._get_order_vals())
        self.assertTrue(order.quotation_ref)
        self.assertRegex(order.quotation_ref, r'^SQ\d{5,}$')
        self.assertEqual(order.state, 'draft')

    def test_03_quotation_ref_is_sequential(self):
        """Verify each new quotation gets a different, increasing reference."""
        first_order = self.sale_order_model.create(self._get_order_vals())
        second_order = self.sale_order_model.create(self._get_order_vals())

        self.assertNotEqual(first_order.quotation_ref,
                            second_order.quotation_ref)
        self.assertGreater(int(second_order.quotation_ref[2:]),
                           int(first_order.quotation_ref[2:]))

    def test_04_quotation_ref_on_multi_create(self):
        """Verify each quotation created in one call gets its own reference."""
        orders = self.sale_order_model.create(
            [self._get_order_vals() for _i in range(3)])

        self.assertEqual(len(orders), 3)
        references = orders.mapped('quotation_ref')
        self.assertTrue(all(references))
        self.assertEqual(len(set(references)), 3)
        for reference in references:
            self.assertRegex(reference, r'^SQ\d{5,}$')

    def test_05_quotation_ref_field_attributes(self):
        """Verify the reference is read only, tracked and not copied."""
        field = self.sale_order_model._fields['quotation_ref']
        self.assertEqual(field.string, 'Quotation Reference')
        self.assertTrue(field.readonly)
        self.assertTrue(field.tracking)
        self.assertFalse(field.copy)

    def test_06_duplicate_gets_new_quotation_ref(self):
        """Verify a duplicated quotation gets a new reference, not a copy."""
        order = self.sale_order_model.create(self._get_order_vals())
        duplicated_order = order.copy()

        self.assertTrue(duplicated_order.quotation_ref)
        self.assertRegex(duplicated_order.quotation_ref, r'^SQ\d{5,}$')
        self.assertNotEqual(duplicated_order.quotation_ref,
                            order.quotation_ref)

    def test_07_quotation_ref_kept_after_confirmation(self):
        """Verify confirming a quotation keeps its reference and order name."""
        order = self.sale_order_model.create(
            self._get_order_vals(with_line=True))
        quotation_ref = order.quotation_ref
        order_name = order.name

        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertEqual(order.quotation_ref, quotation_ref)
        self.assertEqual(order.name, order_name)

    def test_08_form_view_shows_quotation_ref(self):
        """Verify the sale order form view displays the quotation reference
        only for quotations, and the order name only for sale orders.
        """
        arch = self.sale_order_model.get_view(view_type='form')['arch']
        self.assertIn('quotation_ref', arch)
        self.assertIn("state not in ['draft','sent']", arch)
        self.assertIn("state not in ['sale']", arch)

    def test_09_list_view_shows_quotation_ref(self):
        """Verify the quotation list view displays the quotation reference."""
        view = self.env.ref('sale.view_quotation_tree')
        arch = self.sale_order_model.get_view(view_id=view.id)['arch']
        self.assertIn('quotation_ref', arch)

    def test_10_salesman_gets_quotation_ref(self):
        """Verify a salesman can create a quotation and read its reference."""
        salesman = new_test_user(
            self.env, login='separate_quotation_salesman',
            groups='base.group_user,sales_team.group_sale_salesman')

        order = self.sale_order_model.with_user(salesman).create(
            self._get_order_vals())
        self.assertRegex(order.quotation_ref, r'^SQ\d{5,}$')