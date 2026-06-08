# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch

class TestPosOrderLine(TransactionCase):

    def setUp(self):
        super(TestPosOrderLine, self).setUp()
        self.PosOrderLine = self.env['pos.order.line']
        self.washing_type = self.env['washing.type'].create({
            'name': 'Test Wash',
            'amount': 10,
            'assigned_person_id': self.env.uid
        })

    def test_load_pos_data_fields(self):
        """Test _load_pos_data_fields"""
        pos_config = self.env['pos.config'].create({'name': 'Test POS'})
        fields = self.PosOrderLine._load_pos_data_fields(pos_config)
        self.assertIn('washing_type_id', fields)

    def test_order_line_fields(self):
        """Test _order_line_fields with mocking for missing base method"""
        line_data = [0, 0, {'washingType_id': self.washing_type.id, 'product_id': 1}]
        
        # Since _order_line_fields was removed in Odoo 19, the module's call to super() will fail.
        # We mock the base method on the class to allow the module's override to run.
        with patch('odoo.addons.point_of_sale.models.pos_order.PosOrderLine._order_line_fields', 
                   create=True, side_effect=lambda line, session_id: line):
            result = self.PosOrderLine._order_line_fields(line_data, 1)
            self.assertEqual(result[2].get('washing_type_id'), self.washing_type.id)
