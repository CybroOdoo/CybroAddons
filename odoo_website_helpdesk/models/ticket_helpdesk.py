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

from odoo import Command, api, fields, models
from odoo.exceptions import UserError

PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
]
RATING = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
    ('5', 'Extreme High'),
]


class TicketHelpDesk(models.Model):
    """Helpdesk ticket"""
    _name = 'ticket.helpdesk'
    _description = 'Helpdesk Ticket'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _mail_post_access = 'read'

    def _default_stage_id(self):
        """New tickets start in the first stage"""
        return self.env['ticket.stage'].search([], limit=1)

    name = fields.Char(default='New', readonly=True, copy=False,
                       help='Ticket Name')
    customer_id = fields.Many2one('res.partner', help='Customer of the ticket')
    customer_name = fields.Char(help='Name typed by the customer in the '
                                     'website form')
    subject = fields.Text(required=True,
                          help='Subject of the Ticket')
    description = fields.Text(required=True,
                              help='Description')
    email = fields.Char(help='Email')
    phone = fields.Char(help='Contact Number')
    team_id = fields.Many2one('team.helpdesk', string='Helpdesk Team',
                              help='Helpdesk Team Name')
    product_ids = fields.Many2many('product.template',
                                   help='Product Name')
    project_id = fields.Many2one('project.project',
                                 string='Project',
                                 readonly=False,
                                 related='team_id.project_id',
                                 store=True,
                                 help='Project Name')
    priority = fields.Selection(PRIORITIES, default='1', help='Priority of the'
                                                              ' Ticket')
    stage_id = fields.Many2one('ticket.stage', default=lambda self: self._default_stage_id(),
                               tracking=True, index=True,
                               group_expand='_read_group_stage_ids',
                               help='Stages')
    user_id = fields.Many2one('res.users',
                              default=lambda self: self.env.user,
                              index=True, tracking=True,
                              help='User who created the ticket')
    cost = fields.Float('Cost per hour', help='Price of an hour of work on '
                                              'the ticket, used for the '
                                              'invoice')
    service_product_id = fields.Many2one('product.product',
                                         help='Service invoiced for the '
                                              'hours spent on the ticket',
                                         domain=[
                                             ('type', '=', 'service')])
    start_date = fields.Datetime(readonly=True,
                                 help='Date the ticket entered a starting '
                                      'stage')
    end_date = fields.Datetime(readonly=True,
                               help='Date the ticket was closed or canceled')
    public_ticket = fields.Boolean(help='Public Ticket')
    invoice_ids = fields.Many2many('account.move',
                                   string='Invoices',
                                   copy=False,
                                   help='Invoices of the ticket')
    task_ids = fields.Many2many('project.task',
                                string='Tasks',
                                copy=False,
                                help='Tasks of the ticket')
    color = fields.Integer(help='Color')
    replied_date = fields.Datetime('Replied date', readonly=True,
                                   help='Date of the last reply sent to the '
                                        'customer')
    last_update_date = fields.Datetime(readonly=True,
                                       help='Date of the last stage change')
    ticket_type_id = fields.Many2one('helpdesk.type',
                                     help='Ticket Type')
    team_head_id = fields.Many2one('res.users', string='Team Leader',
                                   compute='_compute_team_head_id',
                                   store=True,
                                   help='Team Leader Name')
    assigned_user_id = fields.Many2one('res.users', tracking=True,
                                       domain=[('share', '=', False)],
                                       help='Assigned User Name')
    category_id = fields.Many2one('helpdesk.category', help='Category')
    tags_ids = fields.Many2many('helpdesk.tag', help='Tags')
    attachment_ids = fields.One2many('ir.attachment', 'res_id',
                                     domain=[('res_model', '=',
                                              'ticket.helpdesk')],
                                     help='Files attached to the ticket',
                                     string='Attachments')
    merge_ticket_invisible = fields.Boolean(string='Merge Ticket',
                                            help='Merge Ticket Invisible or '
                                                 'Not', default=False,
                                            copy=False)
    merge_count = fields.Integer(copy=False,
                                 help='Merged Tickets Count')
    active = fields.Boolean(default=True, help='Active')

    show_create_task = fields.Boolean(help='Show created task or not',
                                      compute='_compute_show_create_task')
    create_task = fields.Boolean(string="Create Task", readonly=False,
                                 help='Create task or not',
                                 related='team_id.create_task', store=True)
    billable = fields.Boolean(default=False,
                              help='Is billable or not')
    show_category = fields.Boolean(help='Show category or not',
                                   compute='_compute_show_category')
    customer_rating = fields.Selection(RATING, default='0', readonly=True,
                                       copy=False)
    review = fields.Char(readonly=True, copy=False,
                         help='Ticket review')
    kanban_state = fields.Selection([
        ('normal', 'Ready'),
        ('done', 'In Progress'),
        ('blocked', 'Blocked')], default='normal')

    @api.depends('team_id')
    def _compute_team_head_id(self):
        """The team leader is the leader of the helpdesk team"""
        for ticket in self:
            ticket.team_head_id = ticket.team_id.team_lead_id

    def _compute_show_category(self):
        """Show the category when it is enabled in the settings"""
        show_category = self.env.user.has_group(
            'odoo_website_helpdesk.group_show_category')
        for ticket in self:
            ticket.show_category = show_category

    def _compute_show_create_task(self):
        """Show the task creation when it is enabled in the settings"""
        show_create_task = self.env['ir.config_parameter'].sudo().get_bool(
            'odoo_website_helpdesk.show_create_task')
        for ticket in self:
            ticket.show_create_task = show_create_task

    def _compute_access_url(self):
        """Portal page of the ticket"""
        result = super()._compute_access_url()
        for ticket in self:
            ticket.access_url = f'/my/tickets/{ticket.id}'
        return result

    def _mail_get_partner_fields(self, introspect_fields=False):
        """The customer is the contact of the ticket"""
        return ['customer_id']

    def _get_report_base_filename(self):
        """Name of the PDF of the ticket"""
        self.ensure_one()
        return f'Ticket {self.name}'

    def get_rating_url(self):
        """Link of the rating form sent to the customer"""
        self.ensure_one()
        return (f'{self.get_base_url()}/rating/{self.id}'
                f'?access_token={self._portal_ensure_token()}')

    def _read_group_stage_ids(self, stages, domain):
        """Show all the stages in the kanban view"""
        return stages.search([('active', '=', True)])

    @api.model
    def _stage_values(self, stage):
        """Dates to write when a ticket enters the stage"""
        now = fields.Datetime.now()
        values = {'last_update_date': now}
        if stage.starting_stage:
            values['start_date'] = now
        if stage.closing_stage or stage.cancel_stage:
            values['end_date'] = now
        return values

    @api.model_create_multi
    def create(self, vals_list):
        """Number the tickets and inform the customer and the team"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'ticket.helpdesk') or 'New'
            stage = self.env['ticket.stage'].browse(
                vals.get('stage_id')) or self._default_stage_id()
            vals.update(self._stage_values(stage), stage_id=stage.id)
        tickets = super().create(vals_list)
        tickets._send_template('odoo_website_helpdesk.ticket_created',
                               tickets.filtered('customer_id.email'))
        tickets._notify_team_leader()
        tickets._notify_assigned_user()
        return tickets

    def write(self, vals):
        """Track the stage dates and email the customer, the team leader
        and the assigned user about the changes"""
        old_stages = {}
        if vals.get('stage_id'):
            old_stages = {ticket.id: ticket.stage_id for ticket in self}
            vals = dict(
                vals, **self._stage_values(
                    self.env['ticket.stage'].browse(vals['stage_id'])))
        changed_team = self.filtered(
            lambda t: 'team_id' in vals and t.team_id.id != vals['team_id'])
        changed_user = self.filtered(
            lambda t: 'assigned_user_id' in vals
            and t.assigned_user_id.id != vals['assigned_user_id'])
        result = super().write(vals)
        if old_stages:
            for ticket in self:
                ticket._on_stage_change(old_stages[ticket.id])
        changed_team._notify_team_leader()
        changed_user._notify_assigned_user()
        return result

    def _send_template(self, xml_id, tickets=None):
        """Queue the email of the template for the tickets"""
        template = self.env.ref(xml_id, raise_if_not_found=False)
        if template:
            for ticket in (self if tickets is None else tickets):
                template.sudo().send_mail(ticket.id)

    def _on_stage_change(self, old_stage):
        """Email the template of the new stage, or the reopening email
        when a closed or canceled ticket is opened again"""
        self.ensure_one()
        if old_stage == self.stage_id or not self.customer_id.email:
            return
        if self.stage_id.template_id:
            self.stage_id.template_id.sudo().send_mail(self.id)
        elif ((old_stage.closing_stage or old_stage.cancel_stage)
              and not (self.stage_id.closing_stage
                       or self.stage_id.cancel_stage)):
            self._send_template('odoo_website_helpdesk.ticket_reopened')

    def _notify_team_leader(self):
        """Email the leader of the team given the ticket"""
        self._send_template(
            'odoo_website_helpdesk.odoo_website_helpdesk_assign',
            self.filtered('team_head_id.email'))

    def _notify_assigned_user(self):
        """Email the user assigned to the ticket, and the customer"""
        self._send_template(
            'odoo_website_helpdesk.odoo_website_helpdesk_assign_user',
            self.filtered('assigned_user_id.email'))
        self._send_template(
            'odoo_website_helpdesk.odoo_website_helpdesk_to_customer',
            self.filtered(lambda t: t.assigned_user_id
                          and t.customer_id.email))

    @api.model
    def auto_close_ticket(self):
        """Close the open tickets older than the number of days set in the
        settings"""
        params = self.env['ir.config_parameter'].sudo()
        if not params.get_bool('odoo_website_helpdesk.auto_close_ticket'):
            return
        days = params.get_int('odoo_website_helpdesk.no_of_days')
        close_stage = self.env['ticket.stage'].search(
            [('closing_stage', '=', True)], limit=1)
        if days <= 0 or not close_stage:
            return
        tickets = self.search([
            ('create_date', '<=', fields.Datetime.now() - timedelta(days=days)),
            ('stage_id.closing_stage', '=', False),
            ('stage_id.cancel_stage', '=', False),
        ])
        tickets.write({'stage_id': close_stage.id})

    def action_create_invoice(self):
        """Invoice the hours spent on the tasks of the ticket"""
        self.ensure_one()
        if not self.customer_id:
            raise UserError(self.env._('Set a customer on the ticket before '
                                       'creating the invoice.'))
        if not self.service_product_id:
            raise UserError(self.env._('Set the service product to invoice '
                                       'on the ticket.'))
        tasks = self.env['project.task'].search(
            [('ticket_id', '=', self.id), ('ticket_billed', '=', False)])
        hours = sum(tasks.mapped('effective_hours'))
        if hours <= 0:
            raise UserError(self.env._('There are no timesheet hours to '
                                       'invoice on the tasks of the '
                                       'ticket.'))
        product = self.service_product_id
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'ticket_id': self.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [Command.create({
                'product_id': product.id,
                'quantity': hours,
                'price_unit': self.cost or product.lst_price,
            })],
        })
        tasks.ticket_billed = True
        self.invoice_ids = [Command.link(invoice.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'views': [[False, 'form']],
        }

    def action_create_tasks(self):
        """Create a task for the ticket in the project of its team"""
        self.ensure_one()
        if not self.project_id:
            raise UserError(self.env._('Set a project on the helpdesk team '
                                       'of the ticket to create tasks.'))
        task = self.env['project.task'].create({
            'name': f'{self.name} - {self.subject}',
            'project_id': self.project_id.id,
            'partner_id': self.customer_id.id,
            'description': self.description,
            'ticket_id': self.id,
        })
        self.task_ids = [Command.link(task.id)]
        return {
            'name': self.env._('Tasks'),
            'res_model': 'project.task',
            'res_id': task.id,
            'view_mode': 'form',
            'views': [[False, 'form']],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_open_tasks(self):
        """Open the tasks of the ticket"""
        return {
            'name': self.env._('Tasks'),
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'context': {'default_ticket_id': self.id,
                        'default_project_id': self.project_id.id},
            'type': 'ir.actions.act_window',
        }

    def action_open_invoices(self):
        """Open the invoices of the ticket"""
        return {
            'name': self.env._('Invoices'),
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
        }

    def action_open_merged_tickets(self):
        """Open the tickets merged into this ticket"""
        tickets = self.env['support.ticket'].search(
            [('merged_ticket', '=', self.id)]).ticket_id - self
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Merged Tickets'),
            'view_mode': 'list,form',
            'views': [[False, 'list'], [False, 'form']],
            'res_model': 'ticket.helpdesk',
            'domain': [('id', 'in', tickets.ids)],
            'context': {'active_test': False},
        }

    def action_send_reply(self):
        """Open the email composer with the reply template of the
        settings"""
        self.ensure_one()
        template = self.env['mail.template'].browse(
            self.env['ir.config_parameter'].sudo().get_int(
                'odoo_website_helpdesk.reply_template_id')).exists()
        context = {
            'default_model': 'ticket.helpdesk',
            'default_res_ids': self.ids,
            'default_partner_ids': self.customer_id.ids,
        }
        if template:
            context['default_template_id'] = template.id
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Reply'),
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'views': [[False, 'form']],
            'context': context,
        }
