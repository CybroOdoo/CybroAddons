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

class TestResConfigSettings(TransactionCase):

    def test_res_config_settings_fields(self):
        """Test res.config.settings relation to pos.config field"""
        pos_config = self.env['pos.config'].create({'name': 'Test POS'})
        config = self.env['res.config.settings'].create({
            'pos_config_id': pos_config.id,
            'orderline_washing_type': True,
        })
        config.execute()
        self.assertTrue(pos_config.orderline_washing_type)
