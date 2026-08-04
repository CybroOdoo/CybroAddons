# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests.common import TransactionCase

class TestSaleOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

    def test_01_pet_sitting_action(self):
        """ Test pet_sitting action """
        action = self.sale_order.pet_sitting()
        self.assertTrue(self.sale_order.pet_sittings)
        self.assertEqual(action['res_model'], 'pet.sitting.schedule')
        self.assertEqual(action['context']['default_model_id'], self.sale_order.id)

    def test_02_action_return_meetings(self):
        """ Test action_return_meetings action """
        action = self.sale_order.action_return_meetings()
        self.assertEqual(action['res_model'], 'sitting.schedule')
        self.assertEqual(action['view_mode'], 'calendar')
