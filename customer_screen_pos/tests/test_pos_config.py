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
class TestPosConfig(TransactionCase):
    """Test customer screen fields on pos.config."""

    def test_pos_config_customer_screen_fields(self):
        """POS config stores customer screen options."""
        pos_config = self.env['pos.config'].create({
            'name': 'Customer Screen POS Config',
        })

        self.assertFalse(pos_config.allow_customer_screen)
        self.assertFalse(pos_config.allow_product_click)

        pos_config.write({
            'allow_customer_screen': True,
            'allow_product_click': True,
        })

        self.assertTrue(pos_config.allow_customer_screen)
        self.assertTrue(pos_config.allow_product_click)
