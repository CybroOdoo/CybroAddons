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

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, tagged

from .common import HelpdeskCommon


@tagged('post_install', '-at_install')
class TestHelpdeskTicket(HelpdeskCommon):
    """Tickets, stages, teams, merging and settings of the helpdesk"""

    def test_01_create_ticket(self):
        """A new ticket is numbered, starts in the first stage and the
        customer is emailed"""
        ticket = self._create_ticket()
        self.assertTrue(ticket.name.startswith('TKT'))
        self.assertEqual(ticket.stage_id, self.stage_inbox)
        self.assertTrue(ticket.last_update_date)
        self.assertFalse(ticket.start_date)
        self.assertEqual(ticket.access_url, f'/my/tickets/{ticket.id}')
        mail = self._mails(ticket, f'Ticket {ticket.name} created')
        self.assertEqual(self._recipients(mail), {self.customer.email})
        self.assertIn('/my/tickets/', mail.body_html)
        without_email = self._create_ticket(
            customer_id=self.other_customer.copy({'email': False}).id)
        self.assertFalse(self._mails(
            without_email, f'Ticket {without_email.name} created'))

    def test_02_stage_dates_and_emails(self):
        """The stages save the dates and email the customer, with the
        rating link when the ticket is closed"""
        ticket = self._create_ticket()
        ticket.stage_id = self.stage_progress
        self.assertTrue(ticket.start_date)
        self.assertFalse(ticket.end_date)
        ticket.stage_id = self.stage_done
        self.assertTrue(self._mails(ticket, f'Ticket {ticket.name} solved'))
        ticket.stage_id = self.stage_closed
        self.assertTrue(ticket.end_date)
        mail = self._mails(ticket, f'Ticket {ticket.name} closed')
        self.assertIn(f'/rating/{ticket.id}?access_token='
                      f'{ticket.access_token}', mail.body_html)
        self.assertTrue(ticket.access_token)
        ticket.stage_id = self.stage_progress
        self.assertTrue(self._mails(ticket, f'Ticket {ticket.name} reopened'))
        ticket.stage_id = self.stage_canceled
        self.assertTrue(self._mails(ticket, f'Ticket {ticket.name} canceled'))
        # Writing the same stage again sends nothing
        count = self.env['mail.mail'].sudo().search_count(
            [('model', '=', 'ticket.helpdesk'), ('res_id', '=', ticket.id)])
        ticket.stage_id = self.stage_canceled
        self.assertEqual(self.env['mail.mail'].sudo().search_count(
            [('model', '=', 'ticket.helpdesk'), ('res_id', '=', ticket.id)]),
            count)

    def test_03_team_and_assignment(self):
        """The team leader and the assigned user are emailed, and the
        customer is told who works on the ticket"""
        ticket = self._create_ticket(team_id=self.team.id)
        self.assertEqual(ticket.team_head_id, self.leader)
        self.assertEqual(ticket.project_id, self.project)
        mail = self._mails(ticket,
                           f'Ticket {ticket.name} assigned to your team')
        self.assertEqual(self._recipients(mail), {self.leader.email})
        ticket.assigned_user_id = self.agent
        mail = self._mails(ticket, f'Ticket {ticket.name} assigned to you')
        self.assertEqual(self._recipients(mail), {self.agent.email})
        self.assertTrue(self._mails(ticket, f'Ticket {ticket.name} assigned'))
        other_team = self.env['team.helpdesk'].create({'name': 'Other'})
        ticket.team_id = other_team
        self.assertFalse(ticket.team_head_id)

    def test_04_team_gives_helpdesk_access(self):
        """The leader and the members of a team get the helpdesk access"""
        self.assertTrue(self.leader.has_group(
            'odoo_website_helpdesk.helpdesk_team_leader'))
        self.assertTrue(self.agent.has_group(
            'odoo_website_helpdesk.helpdesk_user'))
        self.assertFalse(self.employee.has_group(
            'odoo_website_helpdesk.helpdesk_user'))
        self.team.member_ids = [(4, self.employee.id)]
        self.assertTrue(self.employee.has_group(
            'odoo_website_helpdesk.helpdesk_user'))

    def test_05_auto_close(self):
        """The old open tickets are closed by the scheduled action"""
        params = self.env['ir.config_parameter'].sudo()
        old = self._create_ticket()
        recent = self._create_ticket()
        canceled = self._create_ticket(stage_id=self.stage_canceled.id)
        self.env.cr.execute(
            "UPDATE ticket_helpdesk SET create_date = %s WHERE id IN %s",
            (fields.Datetime.now() - timedelta(days=10),
             (old.id, canceled.id)))
        self.env.invalidate_all()
        self.Ticket.auto_close_ticket()
        self.assertEqual(old.stage_id, self.stage_inbox)
        params.set_bool('odoo_website_helpdesk.auto_close_ticket', True)
        params.set_int('odoo_website_helpdesk.no_of_days', 0)
        self.Ticket.auto_close_ticket()
        self.assertEqual(old.stage_id, self.stage_inbox)
        params.set_int('odoo_website_helpdesk.no_of_days', 5)
        self.Ticket.auto_close_ticket()
        self.assertEqual(old.stage_id, self.stage_closed)
        self.assertEqual(recent.stage_id, self.stage_inbox)
        self.assertEqual(canceled.stage_id, self.stage_canceled)

    def test_06_create_task(self):
        """Tasks are created in the project of the team"""
        ticket = self._create_ticket()
        with self.assertRaises(UserError):
            ticket.action_create_tasks()
        ticket.team_id = self.team
        action = ticket.action_create_tasks()
        task = self.env['project.task'].browse(action['res_id'])
        self.assertEqual(task.project_id, self.project)
        self.assertEqual(task.ticket_id, ticket)
        self.assertEqual(task.partner_id, self.customer)
        self.assertEqual(ticket.task_ids, task)
        self.assertEqual(ticket.action_open_tasks()['domain'],
                         [('ticket_id', '=', ticket.id)])
        self.assertEqual(ticket.action_open_invoices()['res_model'],
                         'account.move')

    def test_07_merge_into_ticket(self):
        """Merged tickets are archived and listed on the kept ticket"""
        first = self._create_ticket(subject='First', team_id=self.team.id)
        second = self._create_ticket(subject='Second', description='Other')
        tickets = first | second
        wizard_form = Form(self.env['merge.ticket'].with_context(
            active_ids=tickets.ids))
        self.assertEqual(wizard_form.customer_id, self.customer)
        self.assertEqual(wizard_form.support_team_id, self.team)
        wizard_form.support_ticket_id = first
        wizard = wizard_form.save()
        self.assertEqual(len(wizard.support_ticket_ids), 2)
        wizard.action_merge_ticket()
        self.assertFalse(second.active)
        self.assertTrue(first.merge_ticket_invisible)
        self.assertEqual(first.merge_count, 1)
        self.assertIn('Second\n------\nOther', first.description)
        self.assertEqual(wizard.support_ticket_ids.mapped('merged_ticket'),
                         [first.id, first.id])
        action = first.action_open_merged_tickets()
        self.assertEqual(self.Ticket.with_context(active_test=False).search(
            action['domain']), second)

    def test_08_merge_into_new_ticket(self):
        """Tickets can be merged into a new ticket"""
        tickets = self._create_ticket() | self._create_ticket()
        wizard = self.env['merge.ticket'].with_context(
            active_ids=tickets.ids).create({'new_ticket': True})
        with self.assertRaises(UserError):
            wizard.action_merge_ticket()
        wizard.subject = 'Merged'
        action = wizard.action_merge_ticket()
        new_ticket = self.Ticket.browse(action['res_id'])
        self.assertEqual(new_ticket.subject, 'Merged')
        self.assertEqual(new_ticket.merge_count, 2)
        self.assertFalse(any(tickets.mapped('active')))
        empty = self.env['merge.ticket'].create({})
        with self.assertRaises(UserError):
            empty.action_merge_ticket()
        no_target = self.env['merge.ticket'].with_context(
            active_ids=new_ticket.ids).create({})
        with self.assertRaises(UserError):
            no_target.action_merge_ticket()

    def test_09_first_stage_not_deleted(self):
        """The first stage cannot be deleted, the other ones can"""
        with self.assertRaises(UserError):
            self.stage_inbox.unlink()
        stage = self.env['ticket.stage'].create(
            {'name': 'Waiting', 'sequence': 60})
        stage.unlink()
        self.assertFalse(stage.exists())

    def test_10_settings(self):
        """The settings choose the closing stage and show the categories
        and the task creation"""
        ticket = self._create_ticket()
        self.assertFalse(ticket.show_create_task)
        settings = self.env['res.config.settings'].create({})
        self.assertEqual(settings.closed_stage_id, self.stage_closed)
        settings.write({
            'closed_stage_id': self.stage_done.id,
            'group_show_category': True,
            'show_create_task': True,
        })
        settings.execute()
        self.assertTrue(self.stage_done.closing_stage)
        self.assertFalse(self.stage_closed.closing_stage)
        ticket.invalidate_recordset()
        self.assertTrue(ticket.show_create_task)
        self.assertTrue(ticket.with_user(self.agent).show_category)

    def test_11_reply(self):
        """Reply opens the composer with the template of the settings and
        saves the reply date"""
        ticket = self._create_ticket()
        action = ticket.action_send_reply()
        self.assertNotIn('default_template_id', action['context'])
        template = self.env.ref(
            'odoo_website_helpdesk.helpdesk_replay_email_template')
        self.env['ir.config_parameter'].sudo().set_int(
            'odoo_website_helpdesk.reply_template_id', template.id)
        action = ticket.action_send_reply()
        self.assertEqual(action['context']['default_template_id'],
                         template.id)
        composer = self.env['mail.compose.message'].with_context(
            **action['context']).create({})
        composer._action_send_mail()
        self.assertTrue(ticket.replied_date)

    def test_12_website_menu(self):
        """The Helpdesk menu of the website follows the settings"""
        menus = self.env['website.menu'].search(
            [('url', '=', '/helpdesk_ticket')])
        self.assertTrue(menus)
        self.assertFalse(any(menus.mapped('is_visible')))
        self.env['ir.config_parameter'].sudo().set_bool(
            'odoo_website_helpdesk.helpdesk_menu_show', True)
        menus.invalidate_recordset(['is_visible'])
        self.assertTrue(all(menus.mapped('is_visible')))

    def test_13_access(self):
        """The customers read their own tickets only, the employees
        without helpdesk access none, and only the managers configure
        the helpdesk"""
        ticket = self._create_ticket()
        other = self._create_ticket(customer_id=self.other_customer.id)
        Ticket = self.Ticket.with_user(self.portal_user)
        self.assertEqual(Ticket.search([]), ticket)
        with self.assertRaises(AccessError):
            other.with_user(self.portal_user).read(['subject'])
        with self.assertRaises(AccessError):
            ticket.with_user(self.portal_user).write({'subject': 'Changed'})
        with self.assertRaises(AccessError):
            self.Ticket.with_user(self.employee).search([])
        self.assertEqual(self.Ticket.with_user(self.agent).search_count(
            [('id', 'in', (ticket | other).ids)]), 2)
        with self.assertRaises(AccessError):
            self.stage_inbox.with_user(self.agent).write({'name': 'New'})
        self.stage_inbox.with_user(self.manager).write({'name': 'New'})

    def test_14_report(self):
        """The PDF report shows the ticket and its tasks"""
        ticket = self._create_ticket(team_id=self.team.id)
        ticket.action_create_tasks()
        html = self.env['ir.actions.report']._render_qweb_html(
            'odoo_website_helpdesk.report_ticket', ticket.ids)[0]
        self.assertIn(ticket.name.encode(), html)
        self.assertIn(b'Printer broken', html)
        self.assertIn(b'Hours Spent', html)
