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
class TestPosOrderLine(TransactionCase):
    """Tests for the POS order line question fields."""

    def test_question_list_field_exists(self):
        """question_list is available on pos.order.line."""
        field = self.env['pos.order.line']._fields.get('question_list')

        self.assertTrue(field)
        self.assertEqual(field.type, 'text')

    def test_question_list_loaded_in_pos_data_fields(self):
        """question_list is included in POS data loaded fields."""
        fields = self.env['pos.order.line']._load_pos_data_fields(False)
        self.assertIn('question_list', fields)
        self.assertEqual(fields.count('question_list'), 1)
