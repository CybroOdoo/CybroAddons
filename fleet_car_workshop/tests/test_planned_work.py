# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

from odoo.tests import TransactionCase

class TestPlannedWork(TransactionCase):
    """ TestPlannedWork tests """

    def setUp(self):
        """ Setup method """
        super(TestPlannedWork, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Service',
            'lst_price': 200.0,
        })

    def test_planned_work_creation(self):
        """ Test planned.work creation with string description """
        work = self.env['planned.work'].create({
            'planned_work_id': 'Test Service Description',
            'work_cost': 200.0,
        })
        self.assertEqual(work.planned_work_id, 'Test Service Description', "Description should match")
        self.assertEqual(work.work_cost, 200.0, "Cost should match")

    def test_onchange_is_completed(self):
        """ Test _onchange_is_completed function """
        work = self.env['planned.work'].new({
            'time_spent': 5.0,
            'is_completed': True
        })
        work._onchange_is_completed()
        self.assertEqual(work.duration, 5.0, "Duration should match time_spent when completed")
        self.assertTrue(work.work_date2, "Work date should be set")
