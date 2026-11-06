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
from odoo.tests import TransactionCase, new_test_user


class HelpdeskCommon(TransactionCase):
    """Users, team, project and stages used by the helpdesk tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Ticket = cls.env['ticket.helpdesk']
        cls.manager = new_test_user(
            cls.env, login='hd_manager', email='manager@example.com',
            groups='base.group_user,odoo_website_helpdesk.helpdesk_manager')
        cls.leader = new_test_user(
            cls.env, login='hd_leader', email='leader@example.com',
            groups='base.group_user')
        cls.agent = new_test_user(
            cls.env, login='hd_agent', email='agent@example.com',
            groups='base.group_user')
        cls.employee = new_test_user(cls.env, login='hd_employee',
                                     groups='base.group_user')
        cls.portal_user = new_test_user(
            cls.env, login='hd_portal', email='portal@example.com',
            name='Portal Customer', groups='base.group_portal')
        cls.customer = cls.portal_user.partner_id
        cls.other_customer = cls.env['res.partner'].create(
            {'name': 'Other Customer', 'email': 'other@example.com'})
        cls.project = cls.env['project.project'].create(
            {'name': 'Support Project', 'allow_timesheets': True})
        cls.team = cls.env['team.helpdesk'].create({
            'name': 'Support Team',
            'team_lead_id': cls.leader.id,
            'member_ids': [(6, 0, cls.agent.ids)],
            'project_id': cls.project.id,
            'create_task': True,
        })
        cls.stage_inbox = cls.env.ref('odoo_website_helpdesk.stage_inbox')
        cls.stage_progress = cls.env.ref(
            'odoo_website_helpdesk.stage_in_progress')
        cls.stage_done = cls.env.ref('odoo_website_helpdesk.stage_done')
        cls.stage_closed = cls.env.ref('odoo_website_helpdesk.stage_closed')
        cls.stage_canceled = cls.env.ref(
            'odoo_website_helpdesk.stage_canceled')
        cls.ticket_type = cls.env.ref('odoo_website_helpdesk.ticket_type_2')
        cls.category = cls.env.ref('odoo_website_helpdesk.ticket_categories_2')

    @classmethod
    def _create_ticket(cls, **values):
        """Create a ticket of the portal customer"""
        return cls.env['ticket.helpdesk'].create(dict({
            'subject': 'Printer broken',
            'description': 'The printer does not start',
            'customer_id': cls.customer.id,
        }, **values))

    def _recipients(self, mail):
        """Email addresses the mail is sent to"""
        return set(mail.recipient_ids.mapped('email')) | {
            email.strip() for email in (mail.email_to or '').split(',')
            if email.strip()}

    def _mails(self, ticket, subject):
        """Emails queued for the ticket with the subject"""
        return self.env['mail.mail'].sudo().search([
            ('model', '=', 'ticket.helpdesk'), ('res_id', '=', ticket.id),
            ('subject', '=', subject)])
