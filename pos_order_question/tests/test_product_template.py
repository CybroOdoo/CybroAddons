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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Test cases for models/product_template.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Product Template Test Config',
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.uid,
        })
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Product Template Question Test',
            'available_in_pos': True,
            'sale_ok': True,
            'list_price': 12.0,
        })

    def test_order_question_ids_one2many(self):
        """product.template stores linked pos.order.question records in order_question_ids."""
        q1 = self.env['pos.order.question'].create({
            'name': 'Add Sugar?',
            'product_tmpl_id': self.product_tmpl.id,
        })
        q2 = self.env['pos.order.question'].create({
            'name': 'Add Milk?',
            'product_tmpl_id': self.product_tmpl.id,
        })

        self.assertEqual(self.product_tmpl.order_question_ids, q1 | q2)

    def test_load_pos_data_fields_includes_order_question_ids(self):
        """_load_pos_data_fields on product.template includes order_question_ids and base fields."""
        fields_list = self.env['product.template']._load_pos_data_fields(self.pos_config)
        self.assertIn('order_question_ids', fields_list)
        self.assertIn('id', fields_list)
        self.assertIn('name', fields_list)

    def test_session_load_data_includes_order_question_ids_on_product_template(self):
        """session.load_data() returns order_question_ids for product.template."""
        question = self.env['pos.order.question'].create({
            'name': 'Extra Napkins?',
            'product_tmpl_id': self.product_tmpl.id,
        })

        data = self.pos_session.load_data({
            'models': ['product.template', 'pos.order.question'],
            'search_params': {
                'product.template': {'domain': [('id', '=', self.product_tmpl.id)]},
            },
        })
        self.assertIn('order_question_ids', data['product.template']['fields'])
        tmpl_records = {
            rec['id']: rec for rec in data['product.template']['records']
        }
        self.assertIn(self.product_tmpl.id, tmpl_records)
        self.assertIn(
            question.id,
            tmpl_records[self.product_tmpl.id]['order_question_ids'],
        )
