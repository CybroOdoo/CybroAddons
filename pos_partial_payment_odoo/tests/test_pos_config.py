# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.info)
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
from odoo.tests import TransactionCase


class TestPosConfig(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_method = cls.env['pos.payment.method'].create({
            'name': 'Test Pay Later',
            'company_id': cls.env.company.id,
        })
        cls.config = cls.env['pos.config'].create({
            'name': 'Partial Payment Test Config',
            'company_id': cls.env.company.id,
            'partial_payment': True,
            'payment_method_ids': [(6, 0, cls.payment_method.ids)],
        })

    def setUp(self):
        super().setUp()
        self.config = self.__class__.config

    def test_partial_payment_field_defaults_to_true(self):
        config = self.env['pos.config'].create({
            'name': 'Partial Payment Default Config',
            'company_id': self.env.company.id,
            'payment_method_ids': [(6, 0, self.payment_method.ids)],
        })

        self.assertTrue(config.partial_payment)

    def test_partial_payment_can_be_disabled(self):
        self.config.partial_payment = False

        self.assertFalse(self.config.partial_payment)
