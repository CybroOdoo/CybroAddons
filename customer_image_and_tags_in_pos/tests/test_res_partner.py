# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestResPartner(common.TransactionCase):

    def test_load_pos_data_fields(self):
        """Test that category_id is included in the loaded partner fields."""
        pos_config = self.env['pos.config'].search([], limit=1)
        if not pos_config:
            pos_config = self.env['pos.config'].create({'name': 'Test POS Config'})

        fields = self.env['res.partner']._load_pos_data_fields(pos_config)
        self.assertIn('category_id', fields)
