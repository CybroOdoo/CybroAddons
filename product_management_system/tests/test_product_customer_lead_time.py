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

class TestProductCustomerLeadTime(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Lead Time Product 1',
            'sale_delay': 0,
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Lead Time Product 2',
            'sale_delay': 0,
        })

    def test_change_customer_lead_time(self):
        wizard = self.env['product.customer.lead.time'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'sale_delay': 5,
        })
        wizard.action_change_customer_lead_time()
        self.assertEqual(self.product_template_1.sale_delay, 5)
        self.assertEqual(self.product_template_2.sale_delay, 5)
