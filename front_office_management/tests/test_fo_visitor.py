# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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

class TestFoVisitor(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestFoVisitor, cls).setUpClass()
        cls.visitor = cls.env['fo.visitor'].create({
            'name': 'Test Visitor',
            'phone': '1231231234',
            'email': 'visitor2@test.com',
        })
        cls.purpose = cls.env['fo.purpose'].create({
            'name': 'Interview',
        })

    def test_compute_visit_count(self):
        """Test computation of visit count"""
        self.assertEqual(self.visitor.visit_count, 0, "Initial count should be 0")

        visit1 = self.env['fo.visit'].create({
            'visitor_id': self.visitor.id,
            'phone': '1231231234',
            'email': 'visitor2@test.com',
            'reason_ids': [(6, 0, [self.purpose.id])],
        })
        self.visitor.invalidate_recordset(['visit_count'])
        self.assertEqual(self.visitor.visit_count, 1, "Count should be 1 after one visit")

        visit2 = self.env['fo.visit'].create({
            'visitor_id': self.visitor.id,
            'phone': '1231231234',
            'email': 'visitor2@test.com',
            'reason_ids': [(6, 0, [self.purpose.id])],
        })
        self.visitor.invalidate_recordset(['visit_count'])
        self.assertEqual(self.visitor.visit_count, 2, "Count should be 2 after two visits")

        visit2.action_cancel()
        self.visitor.invalidate_recordset(['visit_count'])
        self.assertEqual(self.visitor.visit_count, 1, "Count should be 1 after cancelling one visit")
