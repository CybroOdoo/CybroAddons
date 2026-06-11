# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
class TestResConfigSettings(TransactionCase):
    """Test customer screen settings fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Customer Screen Settings POS Config',
        })

    def test_settings_updates_pos_config_fields(self):
        """Settings related fields update the selected POS config."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'allow_customer_screen': True,
            'allow_product_click': True,
        })

        self.assertTrue(settings.allow_customer_screen)
        self.assertTrue(settings.allow_product_click)
        self.assertTrue(self.pos_config.allow_customer_screen)
        self.assertTrue(self.pos_config.allow_product_click)

    def test_load_pos_data_fields(self):
        """Settings POS load fields include customer screen fields."""
        fields_to_load = self.env['res.config.settings']._load_pos_data_fields(
            self.pos_config.id)

        self.assertIn('allow_customer_screen', fields_to_load)
        self.assertIn('allow_product_click', fields_to_load)
