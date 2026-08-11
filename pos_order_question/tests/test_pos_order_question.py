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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosOrderQuestion(TransactionCase):
    """Tests for POS order question records."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template = cls.env['product.template'].create({
            'name': 'Question Test Product',
        })

    def test_create_pos_order_question(self):
        """A POS order question can be created with a question and product."""
        question = self.env['pos.order.question'].create({
            'name': 'Do you need a bag?',
            'product_tmpl_id': self.product_template.id,
        })
        self.assertEqual(question.name, 'Do you need a bag?')
        self.assertEqual(question.product_tmpl_id, self.product_template)

    def test_question_name_required_by_constraint(self):
        """The model constraint blocks empty question values."""
        with self.assertRaises(ValidationError):
            self.env['pos.order.question'].create({
                'name': False,
                'product_tmpl_id': self.product_template.id,
            })
