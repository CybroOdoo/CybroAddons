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

class TestWashingType(common.TransactionCase):

    def setUp(self):
        super(TestWashingType, self).setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test Laundry User',
            'login': 'test_laundry_user',
        })

    def test_washing_type_creation(self):
        """Test the creation of a washing.type record."""
        washing_type = self.env['washing.type'].create({
            'name': 'Normal Wash',
            'assigned_person_id': self.user.id,
            'amount': 150.0,
        })
        self.assertEqual(washing_type.name, 'Normal Wash')
        self.assertEqual(washing_type.assigned_person_id.id, self.user.id)
        self.assertEqual(washing_type.amount, 150.0)
