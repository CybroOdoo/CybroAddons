# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import TransactionCase, tagged
from unittest.mock import patch


@tagged('post_install', '-at_install')
class TestAllInOneAnnouncements(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAllInOneAnnouncements, cls).setUpClass()
        
        # Enable the email sending setting
        cls.env['ir.config_parameter'].set_param('all_in_one_announcements.is_email', 'True')
        
        # Create a user to be manager
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager@example.com',
            'email': 'test_manager@example.com',
            'groups_id': [(4, cls.env.ref('all_in_one_announcements.announcement_group_manager').id)],
        })
        
        # Create a basic user for task assignment
        cls.task_user = cls.env['res.users'].create({
            'name': 'Task User',
            'login': 'task_user@example.com',
            'email': 'task_user@example.com',
        })
        
        # Set up a project
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project',
        })
        
        # Create an 'In Progress' stage
        cls.stage_in_progress = cls.env['project.task.type'].create({
            'name': 'In Progress',
        })

        # Create a task
        cls.task = cls.env['project.task'].create({
            'name': 'Test Task',
            'project_id': cls.project.id,
            'stage_id': cls.stage_in_progress.id,
            'user_ids': [(4, cls.task_user.id)],
        })

        # Set up a partner
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})

        # Set up a Purchase Order
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.purchase_order.button_confirm() # Changes state to 'purchase'

        # Set up a Sale Order
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.sale_order.action_confirm() # Changes state to 'sale'

        # Create a 'Won' stage for CRM
        cls.stage_won = cls.env['crm.stage'].create({
            'name': 'Won',
            'is_won': True,
        })

        # Set up a CRM Lead
        cls.crm_lead = cls.env['crm.lead'].create({
            'name': 'Test Lead',
            'stage_id': cls.stage_won.id,
        })

    def test_email_send_cron(self):
        """Test the email_send method in res.config.settings which is triggered by cron."""
        settings = self.env['res.config.settings'].create({})
        
        # Ensure the parameter is correctly set and retrieved
        self.env['ir.config_parameter'].sudo().set_param('all_in_one_announcements.is_email', 'True')
        
        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as mock_send_mail:
            settings.email_send()
            self.assertTrue(mock_send_mail.called, "Email should be sent by email_send.")

    def test_task_assigned_rpc(self):
        """Test the task_assigned method in project.task."""
        # Clear outbox before sending
        self.env['mail.mail'].search([]).unlink()
        
        # Ensure the task is not yet marked as announcement sent
        self.assertFalse(self.task.is_announcement_send)
        
        # Call the method
        result = self.env['project.task'].task_assigned()
        
        # Check that it returns structured data
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 4) # Tasks, POs, SOs, CRM
        
        # Verify that task announcement flag is now True
        self.assertTrue(self.task.is_announcement_send)
        
        # Verify that an email was sent to the task assignee
        mail = self.env['mail.mail'].search([('email_to', '=', self.task_user.email)], limit=1)
        self.assertTrue(mail, "Email should be sent to the task assignee.")
        
    def test_get_pending_tasks_project(self):
        """Test the get_pending_tasks method in project.task"""
        action = self.env['project.task'].get_pending_tasks(self.project.id)
        self.assertEqual(action.get('res_model'), 'project.task')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertIn(('id', 'in', self.task.ids), action.get('domain'))

    def test_get_pending_tasks_purchase(self):
        """Test the get_pending_tasks method in purchase.order"""
        action = self.env['purchase.order'].get_pending_tasks(self.purchase_order.id)
        self.assertEqual(action.get('res_model'), 'purchase.order')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertIn(('id', '=', self.purchase_order.id), action.get('domain'))

    def test_get_pending_tasks_sale(self):
        """Test the get_pending_tasks method in sale.order"""
        action = self.env['sale.order'].get_pending_tasks(self.sale_order.id)
        self.assertEqual(action.get('res_model'), 'sale.order')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertIn(('id', '=', self.sale_order.id), action.get('domain'))

    def test_get_pending_tasks_crm(self):
        """Test the get_pending_tasks method in crm.lead"""
        action = self.env['crm.lead'].get_pending_tasks(self.crm_lead.id)
        self.assertEqual(action.get('res_model'), 'crm.lead')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertIn(('id', '=', self.crm_lead.id), action.get('domain'))
