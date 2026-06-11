# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProjectTask(TransactionCase):
    """Unit tests for ProjectTask methods:
    - _compute_volunteer_domain
    - _onchange_project_task_partner_ids
    - write
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.volunteer_partner_1 = cls.env['res.partner'].create({
            'name': 'Volunteer Alice',
            'is_volunteer': True,
        })
        cls.volunteer_partner_2 = cls.env['res.partner'].create({
            'name': 'Volunteer Bob',
            'is_volunteer': True,
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Volunteer Test Project',
            'project_partner_ids': [(6, 0, [
                cls.volunteer_partner_1.id,
                cls.volunteer_partner_2.id,
            ])],
        })

    def test_compute_volunteer_domain(self):
        """Test _compute_volunteer_domain sets task partners from project partners."""
        task = self.env['project.task'].create({
            'name': 'Task with Volunteer Domain',
            'project_id': self.project.id,
        })
        task._compute_volunteer_domain()
        expected_ids = set(self.project.project_partner_ids.ids)
        actual_ids = set(task.project_task_partner_ids.ids)
        self.assertEqual(expected_ids, actual_ids)

    def test_onchange_project_task_partner_ids_adds_follower(self):
        """Test _onchange_project_task_partner_ids subscribes partners as followers."""
        task = self.env['project.task'].create({
            'name': 'Task Follower Onchange',
            'project_id': self.project.id,
        })
        task.project_task_partner_ids = [(6, 0, [self.volunteer_partner_1.id])]
        task._onchange_project_task_partner_ids()

        follower_partner_ids = task.message_follower_ids.mapped('partner_id').ids
        self.assertIn(self.volunteer_partner_1.id, follower_partner_ids)

    def test_write_unsubscribes_removed_partners(self):
        """Test write() unsubscribes partners removed from project_task_partner_ids."""
        task = self.env['project.task'].create({
            'name': 'Task Unsubscribe Write',
            'project_id': self.project.id,
            'project_task_partner_ids': [(6, 0, [
                self.volunteer_partner_1.id,
                self.volunteer_partner_2.id,
            ])],
        })
        task.message_subscribe(partner_ids=[
            self.volunteer_partner_1.id,
            self.volunteer_partner_2.id,
        ])
        follower_ids_before = task.message_follower_ids.mapped('partner_id').ids
        self.assertIn(self.volunteer_partner_1.id, follower_ids_before)
        self.assertIn(self.volunteer_partner_2.id, follower_ids_before)

        task.write({
            'project_task_partner_ids': [(6, 0, [self.volunteer_partner_1.id])],
        })
        task.invalidate_recordset()
        follower_ids_after = task.message_follower_ids.mapped('partner_id').ids
        self.assertIn(self.volunteer_partner_1.id, follower_ids_after)
