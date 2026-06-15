# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
################################################################################
from odoo.tests.common import TransactionCase

class TestProductArchive(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Archive Product 1',
            'active': True,
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Archive Product 2',
            'active': True,
        })

    def test_archive_product(self):
        wizard = self.env['product.archive'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
        })
        wizard.action_archive_product()
        self.assertFalse(self.product_template_1.active)
        self.assertFalse(self.product_template_2.active)
