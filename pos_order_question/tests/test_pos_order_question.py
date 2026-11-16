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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosOrderQuestion(TransactionCase):
    """Test cases for models/pos_order_question.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Question Test Product',
            'available_in_pos': True,
            'list_price': 15.0,
        })

    def test_create_and_read_question(self):
        """Creating a valid pos.order.question sets fields and links to product."""
        question = self.env['pos.order.question'].create({
            'name': 'Extra Spicy?',
            'product_tmpl_id': self.product_tmpl.id,
        })
        self.assertEqual(question.name, 'Extra Spicy?')
        self.assertEqual(question.product_tmpl_id, self.product_tmpl)
        self.assertIn(question, self.product_tmpl.order_question_ids)

    def test_check_name_constraint_on_create(self):
        """Creating a question with an empty or False name raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['pos.order.question'].create({
                'name': '',
                'product_tmpl_id': self.product_tmpl.id,
            })

        with self.assertRaises(ValidationError):
            self.env['pos.order.question'].create({
                'name': False,
                'product_tmpl_id': self.product_tmpl.id,
            })

    def test_check_name_constraint_on_write(self):
        """Updating an existing question to an empty name raises ValidationError."""
        question = self.env['pos.order.question'].create({
            'name': 'No Ice?',
            'product_tmpl_id': self.product_tmpl.id,
        })
        with self.assertRaises(ValidationError):
            question.write({'name': ''})

        with self.assertRaises(ValidationError):
            question.write({'name': False})

    def test_check_name_multi_record(self):
        """_check_name validates every record in a multi-record recordset."""
        questions = self.env['pos.order.question'].create([
            {'name': 'First Question', 'product_tmpl_id': self.product_tmpl.id},
            {'name': 'Second Question', 'product_tmpl_id': self.product_tmpl.id},
        ])
        questions._check_name()

        with self.assertRaises(ValidationError):
            self.env['pos.order.question'].create([
                {'name': 'Valid Question', 'product_tmpl_id': self.product_tmpl.id},
                {'name': '', 'product_tmpl_id': self.product_tmpl.id},
            ])

    def test_pos_load_mixin_inheritance(self):
        """pos.order.question inherits pos.load.mixin methods cleanly."""
        question_model = self.env['pos.order.question']
        self.assertIsInstance(question_model._load_pos_data_domain({}), list)
        self.assertIsInstance(question_model._load_pos_data_fields(None), list)
        self.assertIsInstance(question_model._load_pos_data_dependencies(), list)

    def test_internal_user_crud_access(self):
        """Internal user (base.group_user) has CRUD access to pos.order.question."""
        user = self.env['res.users'].create({
            'name': 'POS Question Test User',
            'login': 'pos_question_test_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        question = self.env['pos.order.question'].with_user(user).create({
            'name': 'Serve Hot?',
            'product_tmpl_id': self.product_tmpl.id,
        })
        self.assertEqual(question.with_user(user).name, 'Serve Hot?')
        question.with_user(user).write({'name': 'Serve Cold?'})
        self.assertEqual(question.name, 'Serve Cold?')
        question.with_user(user).unlink()
        self.assertFalse(question.exists())

