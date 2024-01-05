# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Jumana Haseen (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from odoo.tests import common
_LOGGER = logging.getLogger(__name__)


class TestProductTemplate(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestProductTemplate, cls).setUpClass()
        # create a template
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Product',
            'is_published': True,
            'list_price': 750,
        })

    def test_action_published(self):
        self.product_template.action_published()
        self.assertTrue(self.product_template.is_published)

    def test_action_unpublished(self):
        self.product_template.action_unpublished()
        self.assertFalse(self.product_template.is_published)

    def test_quick_publish_products(self):
        self.product_template.quick_publish_products()
        self.assertFalse(self.product_template.is_published)
