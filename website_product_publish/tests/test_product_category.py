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


class TestProductCategory(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestProductCategory, cls).setUpClass()
        cls.count_01 = cls.env['product.category'].create({
            'name': "New category",
        })
        cls.products_02 = cls.env['product.category'].create(
            {'name': 'Veg'})
        cls.count_02 = cls.env['product.template'].create({'name': 'vegproduct',
                                                        'categ_id':
                                                            cls.products_02.id,
                                                        })

    def test_action_publish_all_products(self):
        self.products_02.action_publish_all_products()
        value = self.count_02.is_published
        message = "Product is published"
        self.assertTrue(value, message)
