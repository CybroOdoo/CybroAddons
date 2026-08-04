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
from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase

class TestPetWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Walker',
            'is_walker_sitters': True,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.wizard = self.env['pet.sitting.schedule'].create({
            'walker_sitting_id': self.employee.id,
            'date_start': datetime.now(),
            'end_date': datetime.now() + timedelta(hours=1),
            'reference_id': self.sale_order.id,
        })

    def test_01_assign_sittings(self):
        """ Test assign_sittings method """
        self.wizard.assign_sittings()
        schedule = self.env['sitting.schedule'].search([('number_id', '=', self.sale_order.id)])
        self.assertTrue(schedule)
        self.assertEqual(schedule.name, 'Meeting')
        self.assertIn(self.employee, schedule.attendees_ids)
