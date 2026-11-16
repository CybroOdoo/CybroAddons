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
class TestPosSession(TransactionCase):
    """Test cases for models/pos_session.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'POS Session Test Config',
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.uid,
        })
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Session Question Product',
            'available_in_pos': True,
            'sale_ok': True,
            'list_price': 10.0,
        })

    def test_load_pos_data_models_contains_question_and_product_template(self):
        """_load_pos_data_models includes pos.order.question and product.template without duplicates."""
        models_list = self.env['pos.session']._load_pos_data_models(self.pos_config)
        self.assertIn('pos.order.question', models_list)
        self.assertIn('product.template', models_list)
        self.assertEqual(models_list.count('pos.order.question'), 1)
        self.assertEqual(models_list.count('product.template'), 1)

    def test_session_load_data_includes_pos_order_question_records(self):
        """session.load_data() includes pos.order.question and its records."""
        question = self.env['pos.order.question'].create({
            'name': 'Gift Wrap?',
            'product_tmpl_id': self.product_tmpl.id,
        })

        data = self.pos_session.load_data({
            'models': ['pos.order.question', 'product.template'],
            'search_params': {
                'product.template': {'domain': [('id', '=', self.product_tmpl.id)]},
            },
        })
        self.assertIn('pos.order.question', data)
        self.assertIn('product.template', data)
        loaded_ids = [rec['id'] for rec in data['pos.order.question']['records']]
        self.assertIn(question.id, loaded_ids)
