# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#     Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author: Anaswara S (odoo@cybrosys.com)
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
from odoo.tests import common

class TestWashingWork(common.TransactionCase):

    def setUp(self):
        super(TestWashingWork, self).setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test Laundry Worker',
            'login': 'test_laundry_worker',
        })

    def test_washing_work_creation(self):
        """Test the creation of a washing.work record."""
        washing_work = self.env['washing.work'].create({
            'name': 'Ironing',
            'assigned_person_id': self.user.id,
            'amount': 50.0,
        })
        self.assertEqual(washing_work.name, 'Ironing')
        self.assertEqual(washing_work.assigned_person_id.id, self.user.id)
        self.assertEqual(washing_work.amount, 50.0)
