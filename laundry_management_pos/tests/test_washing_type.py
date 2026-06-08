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

class TestWashingType(TransactionCase):

    def test_pos_data_methods(self):
        """Test _load_pos_data_fields, _load_pos_data_domain, _load_pos_data_search_read"""
        WashingType = self.env['washing.type']
        pos_config = self.env['pos.config'].create({'name': 'Test POS'})
        fields = WashingType._load_pos_data_fields(pos_config)
        self.assertIn('name', fields)
        
        domain = WashingType._load_pos_data_domain({})
        self.assertEqual(domain, [])
        
        res = WashingType._load_pos_data_search_read({}, pos_config)
        self.assertIsInstance(res, list)
