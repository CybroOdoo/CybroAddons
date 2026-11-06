# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo.tests import TransactionCase
from datetime import date, timedelta


class TestCommissionPlanInherit(TransactionCase):

    def setUp(self):
        super(TestCommissionPlanInherit, self).setUp()
        self.commission = self.env['crm.commission'].create({
            'name': 'Inherit Plan',
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=10),
            'type': 'product',
        })

    def test_crm_team_inherit(self):
        """Test inheritance of commission plan in crm_team"""
        team = self.env['crm.team'].create({
            'name': 'Test Team',
            'commission_id': self.commission.id,
        })
        self.assertEqual(team.commission_id.id, self.commission.id)

    def test_res_users_inherit(self):
        """Test inheritance of commission plan in res.users"""
        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_comm',
            'commission_id': self.commission.id,
        })
        self.assertEqual(user.commission_id.id, self.commission.id)
