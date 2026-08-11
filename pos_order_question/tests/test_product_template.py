# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Tests for product template POS order question fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template = cls.env['product.template'].create({
            'name': 'Product Template Question Test',
        })
        cls.question = cls.env['pos.order.question'].create({
            'name': 'Add gift wrap?',
            'product_tmpl_id': cls.product_template.id,
        })

    def test_order_question_ids_relation(self):
        """Product template links to its POS order questions."""

        self.assertIn(self.question, self.product_template.order_question_ids)
        self.assertEqual(
            self.question.product_tmpl_id,
            self.product_template,
        )

    def test_order_question_ids_loaded_in_pos_data_fields(self):
        """order_question_ids is included in POS data loaded fields."""
        fields = self.env['product.template']._load_pos_data_fields(False)

        self.assertIn('order_question_ids', fields)
        self.assertEqual(fields.count('order_question_ids'), 1)
