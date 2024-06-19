# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

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
    ('5', 'Extreme High')
]


class HelpTicket(models.Model):
    """This model represents the Helpdesk Ticket, which allows users to raise
    tickets related to products, services or any other issues. Each ticket has a
    name, customer information, description, team responsible for handling
    requests, associated project, priority level, stage, cost per hour, service
    product, start and end dates, and related tasks and invoices."""

    _name = 'help.ticket'
    _description = 'Help Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: _('New'),
                       help='The name of the help ticket. By default, a new '
                            'unique sequence number is assigned to each '
                            'help ticket, unless a name is provided.',
                       readonly=True)
    active = fields.Boolean(default=True, help='Active', string='Active')
    customer_id = fields.Many2one('res.partner',
                                  string='Customer Name',
                                  help='Select the Customer Name')
    customer_name = fields.Char(string='Customer Name',
                                help='Add the Customer Name')
    subject = fields.Text(string='Subject', required=True,
                          help='Subject of the Ticket')
    description = fields.Text(string='Description', required=True,
                              help='Issue Description')
    email = fields.Char(string='Email', help='Email of the User.')
    phone = fields.Char(string='Phone', help='Phone Number of the user')
    team_id = fields.Many2one('help.team', string='Helpdesk Team',
                              help='The helpdesk team responsible for '
                                   'handling requests related to this '
                                   'record')
    product_ids = fields.Many2many('product.template',
                                   string='Product',
                                   help='The product associated with this '
                                        'record.This field allows you to select'
                                        'an existing product from the product '
                                        'catalog.')
    project_id = fields.Many2one('project.project',
                                 string='Project',
                                 readonly=False,
                                 related='team_id.project_id',
                                 store=True,
                                 help='The project associated with this team.'
                                      'This field is automatically filled '
                                      'based on the project assigned to '
                                      'the team.')
    priority = fields.Selection(PRIORITIES,
                                default='1',
                                help='Set the priority level',
                                string='Priority')
    stage_id = fields.Many2one('ticket.stage', string='Stage',
                               default=lambda self: self.env[
                                   'ticket.stage'].search(
                                   [('name', '=', 'Draft')], limit=1).id,
                               tracking=True,
                               group_expand='_read_group_stage_ids',
                               help='Stages of the ticket.')
    user_id = fields.Many2one('res.users',
                              default=lambda self: self.env.user,
                              check_company=True,
                              index=True, tracking=True,
                              help='Login User')
    cost = fields.Float(string='Cost per hour',
                        help='The cost per hour for this record. This field '
                             'specifies the hourly cost associated with the'
                             'record, which can be used in various '
                             'calculations or reports.')
    service_product_id = fields.Many2one('product.product',
                                         string='Service Product',
                                         help='The product associated with this'
                                              'service. Only service products '
                                              'are available for selection.',
                                         domain=[
                                             ('detailed_type', '=', 'service')])
    create_date = fields.Datetime(string='Creation Date', help='Created date of'
                                                               'the Ticket')
    start_date = fields.Datetime(string='Start Date', help='Start Date of the '
                                                           'Ticket')
    end_date = fields.Datetime(string='End Date', help='End Date of the Ticket')
    public_ticket = fields.Boolean(string="Public Ticket", help='Public Ticket')
    invoice_ids = fields.Many2many('account.move',
                                   string='Invoices',
                                   help='To Generate Invoice based on hours '
                                        'spent on the ticket'
                                   )
    task_ids = fields.Many2many('project.task',
                                string='Tasks',
                                help='Related Task of the Ticket')
    color = fields.Integer(string="Color", help='Color')
    replied_date = fields.Datetime(string='Replied date',
                                   help='Replied Date of the Ticket')
    last_update_date = fields.Datetime(string='Last Update Date',
                                       help='Last Update Date of Ticket')
    ticket_type = fields.Many2one('helpdesk.types',
                                  string='Ticket Type', help='Ticket Type')
    team_head = fields.Many2one('res.users', string='Team Leader',
                                compute='_compute_team_head',
                                help='Team Leader Name')
    assigned_user = fields.Many2one(
        'res.users',
        string='Assigned User',
        domain=lambda self: [('groups_id', 'in', self.env.ref(
            'odoo_website_helpdesk.helpdesk_user').id)],
        help='Choose the Assigned User Name')
    category_id = fields.Many2one('helpdesk.categories',
                                  help='Choose the Category', string='Category')
    tags = fields.Many2many('helpdesk.tag', help='Choose the Tags',
                            string='Tag')
    assign_user = fields.Boolean(string='Assigned User', help='Assign User')
    attachment_ids = fields.One2many('ir.attachment',
                                     'res_id',
                                     help='Attachment Line',
                                     string='Attachment')
    merge_ticket_invisible = fields.Boolean(string='Merge Ticket',
                                            help='Merge Ticket Invisible or '
                                                 'Not')
    merge_count = fields.Integer(string='Merge Count', help='Merged Tickets '
                                                           'Count')

    @api.onchange('team_id', 'team_head')
    def team_leader_domain(self):
        """Update the domain for the assigned user based on the selected team.

        This onchange method is triggered when the helpdesk team or team leader
        is changed. It updates the domain for the assigned user field to include
        only the members of the selected team."""
        teams = []
        for rec in self.team_id.member_ids:
            teams.append(rec.id)
        return {'domain': {'assigned_user': [('id', 'in', teams)]}}

    @api.depends('team_id')
    def _compute_team_head(self):
        """Compute the team head based on the selected team.

        This method is triggered when the helpdesk team is changed. It computes
        and updates the team head field based on the team's lead.
       """
        self.team_head = self.team_id.team_lead_id.id

    @api.onchange('stage_id')
    def mail_snd(self):
        """Send an email when the stage of the ticket is changed.

        This onchange method is triggered when the stage of the ticket is
        changed. It updates the last update date, start date, and end date
        fields accordingly. If a template is associated with the stage, it
        sends an email using that template."""
        rec_id = self._origin.id
        data = self.env['help.ticket'].search([('id', '=', rec_id)])
        data.last_update_date = fields.Datetime.now()
        if self.stage_id.starting_stage:
            data.start_date = fields.Datetime.now()
        if self.stage_id.closing_stage or self.stage_id.cancel_stage:
            data.end_date = fields.Datetime.now()
        if self.stage_id.template_id:
            mail_template = self.stage_id.template_id
            mail_template.send_mail(self._origin.id, force_send=True)

    def assign_to_teamleader(self):
        """Assign the ticket to the team leader and send a notification.

        This function checks if a helpdesk team is selected and assigns the
        team leader to the ticket. It then sends a notification email to the
        team leader."""
        if self.team_id:
            self.team_head = self.team_id.team_lead_id.id
            mail_template = self.env.ref(
                'odoo_website_helpdesk.'
                'mail_template_odoo_website_helpdesk_assign')
            mail_template.sudo().write({
                'email_to': self.team_head.email,
                'subject': self.name
            })
            mail_template.sudo().send_mail(self.id, force_send=True)
        else:
            raise ValidationError("Please choose a Helpdesk Team")

    def _default_show_create_task(self):
        """Get the default value for the 'show_create_task' field.

        This method retrieves the default value for the 'show_create_task'
        field from the configuration settings."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_create_task')

    show_create_task = fields.Boolean(string="Create Task",
                                      default=_default_show_create_task,
                                      compute='_compute_show_create_task',
                                      help='Determines whether the Create Task'
                                           ' button should be shown for this '
                                           'ticket.')
    create_task = fields.Boolean(string="Create Task", readonly=False,
                                 related='team_id.create_task',
                                 store=True,
                                 help='Defines if a task should be created when'
                                      ' this ticket is created.')
    billable = fields.Boolean(string="Billable", help='Indicates whether the '
                                                      'ticket is billable or '
                                                      'not.')

    def _default_show_category(self):
        """Its display the default category"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_category')

    show_category = fields.Boolean(default=_default_show_category,
                                   compute='_compute_show_category',
                                   help='Display the default category')
    customer_rating = fields.Selection(RATING, default='0', readonly=True,
                                       string='Customer Rating',
                                       help='Display the customer rating.')

    review = fields.Char(string='Review', readonly=True,
                         help='Customer review of the ticket.')
    kanban_state = fields.Selection([
        ('normal', 'Ready'),
        ('done', 'In Progress'),
        ('blocked', 'Blocked'), ], default='normal')

    def _compute_show_category(self):
        """Compute show category"""
        show_category = self._default_show_category()
        for rec in self:
            rec.show_category = show_category

    def _compute_show_create_task(self):
        """Compute the value of the 'show_create_task' field for each record in
        the current recordset."""
        show_create_task = self._default_show_create_task()
        for record in self:
            record.show_create_task = show_create_task

    def auto_close_ticket(self):
        """Automatically closing the ticket based on the closing date."""
        auto_close = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.auto_close_ticket')
        if auto_close:
            no_of_days = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_website_helpdesk.no_of_days')
            records = self.env['help.ticket'].search([])
            for rec in records:
                days = (fields.Datetime.today() - rec.create_date).days
                if days >= int(no_of_days):
                    close_stage_id = self.env['ticket.stage'].search(
                        [('closing_stage', '=', True)])
                    if close_stage_id:
                        rec.stage_id = close_stage_id

    def default_stage_id(self):
        """Search your stage"""
        return self.env['ticket.stage'].search(
            [('name', '=', 'Draft')], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        Return the available stages for grouping.

        This static method is used to provide the available stages for
        grouping when displaying records in a grouped view.

        """
        stage_ids = self.env['ticket.stage'].search([])
        return stage_ids

    @api.model
    def create(self, vals_list):
        """Create a new helpdesk ticket.
        This method is called when creating a new helpdesk ticket. It
        generates a unique name for the ticket using a sequence if no
        name is provided.
        """
        if vals_list.get('name', _('New')) == _('New'):
            vals_list['name'] = self.env['ir.sequence'].next_by_code(
                'help.ticket') or _('New')
        return super().create(vals_list)

    def action_create_invoice(self):
        """Create Invoice for Help Desk Ticket.
        This function creates an invoice for the help desk ticket based on
        the associated tasks with billed hours.
        """
        tasks = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id),
             ('ticket_id', '=', self.id)]).filtered(
            lambda line: line.ticket_billed == True)
        if not tasks:
            raise UserError('No Tasks to Bill')
        total = sum(x.effective_hours for x in tasks if x.effective_hours > 0)
        invoice_no = self.env['ir.sequence'].next_by_code(
            'ticket.invoice')
        self.env['account.move'].create([
            {
                'name': invoice_no,
                'move_type': 'out_invoice',
                'partner_id': self.customer_id.id,
                'ticket_id': self.id,
                'date': fields.Date.today(),
                'invoice_date': fields.Date.today(),
                'invoice_line_ids':
                    [(0, 0, {'product_id': self.service_product_id.id,
                             'name': self.service_product_id.name,
                             'quantity': total,
                             'product_uom_id': self.service_product_id.uom_id.id,
                             'price_unit': self.cost,
                             'account_id':
                                 self.service_product_id.categ_id.property_account_income_categ_id.id,
                             })],
            }, ])
        for task in tasks:
            task.ticket_billed = True
        return {
            'effect': {
                'fadeout': 'medium',
                'message': 'Billed Successfully!',
                'type': 'rainbow_man',
            }
        }

    def action_create_tasks(self):
        """Create Task for HelpDesk Ticket
        This function creates a task associated with the helpdesk ticket
        and updates the task_ids field.
        """
        task_id = self.env['project.task'].create({
            'name': self.name + '-' + self.subject,
            'project_id': self.project_id.id,
            'company_id': self.env.company.id,
            'ticket_id': self.id,
        })
        self.write({
            'task_ids': [(4, task_id.id)]
        })
        return {
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_id': False,
            'res_id': task_id.id,
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_open_tasks(self):
        """Smart Button of Task to view the Tasks of HelpDesk Ticket"""
        return {
            'name': 'Tasks',
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'project.task',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def action_open_invoices(self):
        """Smart Button of Invoice to view the Invoices for HelpDesk Ticket"""
        return {
            'name': 'Invoice',
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def action_open_merged_tickets(self):
        """ Smart button of the merged tickets"""
        ticket_ids = self.env['support.tickets'].search(
            [('merged_ticket', '=', self.id)])
        # Get the display_name matching records from the support.tickets
        helpdesk_ticket_ids = ticket_ids.mapped('display_name')
        # Get the IDs of the help.ticket records matching the display names
        help_ticket_records = self.env['help.ticket'].search(
            [('name', 'in', helpdesk_ticket_ids)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Helpdesk Ticket',
            'view_mode': 'tree,form',
            'res_model': 'help.ticket',
            'domain': [('id', 'in', help_ticket_records.ids)],
            'context': self.env.context,
        }

    def action_send_reply(self):
        """Compose and send a reply to the customer.
        This function opens a window for composing and sending a reply to
        the customer. It uses the configured email template for replies.
       """
        template_id = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.reply_template_id'
        )
        template_id = self.env['mail.template'].browse(int(template_id))
        if template_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'mail',
                'res_model': 'mail.compose.message',
                'view_mode': 'form',
                'target': 'new',
                'views': [[False, 'form']],
                'context': {
                    'default_model': 'help.ticket',
                    'default_res_id': self.id,
                    'default_template_id': template_id.id
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'mail',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_model': 'help.ticket',
                'default_res_id': self.id,
            }
        }
