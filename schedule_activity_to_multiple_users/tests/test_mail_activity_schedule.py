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
#############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMailActivityScheduleMultipleUsers(TransactionCase):
    """Test suite for scheduling activities to multiple users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.activity_type = (
            cls.env.ref(
                'mail.mail_activity_data_todo', raise_if_not_found=False
            )
            or cls.env['mail.activity.type'].search([], limit=1)
        )
        if not cls.activity_type:
            cls.activity_type = cls.env['mail.activity.type'].create({
                'name': 'To Do',
                'category': 'default',
                'delay_count': 0,
            })

        cls.user_1 = cls.env['res.users'].create({
            'name': 'Test User 1',
            'login': 'test_user_1',
            'email': 'user1@test.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.user_2 = cls.env['res.users'].create({
            'name': 'Test User 2',
            'login': 'test_user_2',
            'email': 'user2@test.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.user_3 = cls.env['res.users'].create({
            'name': 'Test User 3',
            'login': 'test_user_3',
            'email': 'user3@test.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'partner1@test.com',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Test Partner 2',
            'email': 'partner2@test.com',
        })

    def test_schedule_activity_multiple_users_on_record(self):
        """Schedule activity for main user and multiple assigned users."""
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': f'[{self.partner_1.id}]',
            'activity_type_id': self.activity_type.id,
            'activity_user_id': self.user_1.id,
            'assign_multiple_user_ids': [
                (6, 0, [self.user_2.id, self.user_3.id])
            ],
            'summary': 'Team Sync',
            'note': '<p>Discuss project progress</p>',
            'date_deadline': fields.Date.today(),
        })
        result = wizard._action_schedule_activities()

        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner_1.id),
            ('summary', '=', 'Team Sync'),
        ])
        self.assertEqual(len(activities), 3)
        self.assertEqual(
            set(activities.mapped('user_id')),
            {self.user_1, self.user_2, self.user_3},
        )
        for act in activities:
            self.assertEqual(act.activity_type_id, self.activity_type)
            self.assertEqual(act.note, '<p>Discuss project progress</p>')
            self.assertEqual(act.date_deadline, fields.Date.today())

        # When activity_user_id is in scheduled records, return that record
        self.assertEqual(result.user_id, self.user_1)

    def test_schedule_activity_action_button(self):
        """Test action_schedule_activities action button."""
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': f'[{self.partner_1.id}]',
            'activity_type_id': self.activity_type.id,
            'activity_user_id': self.user_1.id,
            'assign_multiple_user_ids': [(6, 0, [self.user_2.id])],
            'summary': 'Action Button Test',
            'date_deadline': fields.Date.today(),
        })
        wizard.action_schedule_activities()

        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner_1.id),
            ('summary', '=', 'Action Button Test'),
        ])
        self.assertEqual(len(activities), 2)

    def test_schedule_activity_single_user(self):
        """Schedule activity when no multiple users are assigned."""
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': f'[{self.partner_1.id}]',
            'activity_type_id': self.activity_type.id,
            'activity_user_id': self.user_1.id,
            'summary': 'Solo Task',
            'date_deadline': fields.Date.today(),
        })
        result = wizard._action_schedule_activities()

        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner_1.id),
            ('summary', '=', 'Solo Task'),
        ])
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id, self.user_1)
        self.assertEqual(result, activities)

    def test_schedule_activity_only_multiple_users_no_main_user(self):
        """Schedule activity when activity_user_id is False."""
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': f'[{self.partner_1.id}]',
            'activity_type_id': self.activity_type.id,
            'activity_user_id': False,
            'assign_multiple_user_ids': [
                (6, 0, [self.user_2.id, self.user_3.id])
            ],
            'summary': 'Delegated Task',
            'date_deadline': fields.Date.today(),
        })
        result = wizard._action_schedule_activities()

        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner_1.id),
            ('summary', '=', 'Delegated Task'),
        ])
        self.assertEqual(len(activities), 2)
        self.assertEqual(
            set(activities.mapped('user_id')),
            {self.user_2, self.user_3},
        )
        self.assertEqual(set(result.ids), set(activities.ids))

    def test_schedule_activity_user_deduplication(self):
        """Ensure duplicate user in assign_multiple_user_ids is handled."""
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': f'[{self.partner_1.id}]',
            'activity_type_id': self.activity_type.id,
            'activity_user_id': self.user_1.id,
            'assign_multiple_user_ids': [
                (6, 0, [self.user_1.id, self.user_2.id])
            ],
            'summary': 'Deduplication Check',
            'date_deadline': fields.Date.today(),
        })
        wizard.action_schedule_activities()

        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner_1.id),
            ('summary', '=', 'Deduplication Check'),
        ])
        self.assertEqual(len(activities), 2)
        self.assertEqual(
            set(activities.mapped('user_id')),
            {self.user_1, self.user_2},
        )

    def test_schedule_activity_multiple_records(self):
        """Schedule activity for multiple partners and multiple users."""
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': f'[{self.partner_1.id}, {self.partner_2.id}]',
            'activity_type_id': self.activity_type.id,
            'activity_user_id': self.user_1.id,
            'assign_multiple_user_ids': [(6, 0, [self.user_2.id])],
            'summary': 'Bulk Partner Activity',
            'date_deadline': fields.Date.today(),
        })
        wizard.action_schedule_activities()

        for partner in (self.partner_1, self.partner_2):
            acts = self.env['mail.activity'].search([
                ('res_model', '=', 'res.partner'),
                ('res_id', '=', partner.id),
                ('summary', '=', 'Bulk Partner Activity'),
            ])
            self.assertEqual(len(acts), 2)
            self.assertEqual(
                set(acts.mapped('user_id')),
                {self.user_1, self.user_2},
            )

    def test_schedule_personal_activity_multiple_users(self):
        """Schedule personal activities (no res_model) for multiple users."""
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': False,
            'activity_type_id': self.activity_type.id,
            'activity_user_id': self.user_1.id,
            'assign_multiple_user_ids': [(6, 0, [self.user_2.id])],
            'summary': 'Personal Note',
            'note': '<p>Personal reminder</p>',
            'date_deadline': fields.Date.today(),
        })
        wizard.action_schedule_activities()

        personal_acts = self.env['mail.activity'].search([
            ('res_model_id', '=', False),
            ('res_id', '=', False),
            ('summary', '=', 'Personal Note'),
        ])
        self.assertEqual(len(personal_acts), 2)
        self.assertEqual(
            set(personal_acts.mapped('user_id')),
            {self.user_1, self.user_2},
        )

    def test_action_schedule_activities_done(self):
        """Test action_schedule_activities_done with multiple users."""
        wizard = self.env['mail.activity.schedule'].create({
            'res_model': 'res.partner',
            'res_ids': f'[{self.partner_1.id}]',
            'activity_type_id': self.activity_type.id,
            'activity_user_id': self.user_1.id,
            'assign_multiple_user_ids': [(6, 0, [self.user_2.id])],
            'summary': 'Complete Right Away',
            'date_deadline': fields.Date.today(),
        })
        wizard.action_schedule_activities_done()

        # The returned activity for user_1 is marked done
        user_1_act = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner_1.id),
            ('summary', '=', 'Complete Right Away'),
            ('user_id', '=', self.user_1.id),
        ])
        self.assertFalse(user_1_act)

        # The activity for user_2 remains open
        user_2_act = self.env['mail.activity'].search([
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.partner_1.id),
            ('summary', '=', 'Complete Right Away'),
            ('user_id', '=', self.user_2.id),
        ])
        self.assertEqual(len(user_2_act), 1)

    def test_assign_multiple_users_field_definition(self):
        """Verify field definition and attributes on mail.activity.schedule."""
        field = self.env['mail.activity.schedule']._fields.get(
            'assign_multiple_user_ids'
        )
        self.assertTrue(field)
        self.assertEqual(field.type, 'many2many')
        self.assertEqual(field.comodel_name, 'res.users')
        self.assertEqual(
            field.string, 'Assign Multiple Users'
        )
