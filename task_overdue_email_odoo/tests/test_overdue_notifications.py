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
#############################################################################
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOverdueNotifications(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env['project.project'].create({
            'name': 'Overdue Notification Test Project',
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Overdue Notification User',
            'login': 'overdue_notification_user',
            'email': 'overdue@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_action_overdue_skips_tasks_in_native_closed_states(self):
        now = fields.Datetime.now()
        common_values = {
            'project_id': self.project.id,
            'date_deadline': now,
            'user_ids': [(6, 0, [self.user.id])],
        }
        open_task = self.env['project.task'].create(
            dict(common_values, name='Open overdue task')
        )
        self.env['project.task'].create([
            dict(common_values, name='Done overdue task', state='1_done'),
            dict(common_values, name='Cancelled overdue task', state='1_canceled'),
        ])
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('task_overdue_email_odoo.is_notification', True)
        params.set_int('task_overdue_email_odoo.overdue_days', 0)

        template_model = type(self.env['mail.template'])
        with patch.object(template_model, 'send_mail', return_value=1) as send_mail:
            with patch('odoo.fields.Datetime.now', return_value=now):
                self.env['project.task'].action_overdue()

        user_calls = [
            call for call in send_mail.call_args_list
            if call.kwargs.get('email_values', {}).get('email_to') == self.user.email
        ]
        self.assertEqual(len(user_calls), 1)
        self.assertEqual(user_calls[0].args[0], open_task.id)

    def test_action_overdue_disabled_notification(self):
        now = fields.Datetime.now()
        self.env['project.task'].create({
            'name': 'Open overdue task',
            'project_id': self.project.id,
            'date_deadline': now,
            'user_ids': [(6, 0, [self.user.id])],
        })
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('task_overdue_email_odoo.is_notification', False)

        template_model = type(self.env['mail.template'])
        with patch.object(template_model, 'send_mail', return_value=1) as send_mail:
            self.env['project.task'].action_overdue()

        self.assertEqual(send_mail.call_count, 0)

    def test_action_overdue_days_filtering(self):
        now = fields.Datetime.now()
        three_days_ago = now - timedelta(days=3)
        task_overdue_3_days = self.env['project.task'].create({
            'name': 'Task overdue 3 days',
            'project_id': self.project.id,
            'date_deadline': three_days_ago,
            'user_ids': [(6, 0, [self.user.id])],
        })
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('task_overdue_email_odoo.is_notification', True)
        params.set_int('task_overdue_email_odoo.overdue_days', 3)

        template_model = type(self.env['mail.template'])
        with patch.object(template_model, 'send_mail', return_value=1) as send_mail:
            with patch('odoo.fields.Datetime.now', return_value=now):
                self.env['project.task'].action_overdue()

        user_calls = [
            call for call in send_mail.call_args_list
            if call.kwargs.get('email_values', {}).get('email_to') == self.user.email
        ]
        self.assertEqual(len(user_calls), 1)
        self.assertEqual(user_calls[0].args[0], task_overdue_3_days.id)
