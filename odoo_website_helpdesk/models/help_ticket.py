# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High')]


class HelpDeskTicket(models.Model):
    """This model represents the Helpdesk Ticket, which allows users to raise
    tickets related to products, services or any other issues. Each ticket has a
    name, customer information, description, team responsible for handling
    requests, associated project, priority level, stage, cost per hour, service
    product, start and end dates, and related tasks and invoices."""

    _name = 'help.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_show_create_task(self):
        """Get the value for the 'show_create_task' field in config settings."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_create_task')

    name = fields.Char(string='Name', default=lambda self: self.env['ir'
                                                                    '.sequence']
                       .next_by_code('help.ticket') or _('New'),
                       help='The name of the help ticket. By default, a new '
                            'unique sequence number is assigned to each '
                            'help ticket, unless a name is provided.')
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  help="Select the Customer",
                                  domain="[('type', '!=', 'private')]")
    customer_name = fields.Char(string='Customer Name', help="Add the "
                                                             "Customer Name")
    subject = fields.Text('Subject', required=True,
                          help="Subject of the Ticket")
    description = fields.Text('Description', required=True, help="Issue "
                                                                 "Description")
    email = fields.Char(string='Email', help=" Email of the user")
    phone = fields.Char(string='Phone', help="Phone Number of the user")
    team_id = fields.Many2one('help.team', string='Helpdesk Team',
                              help="The helpdesk team responsible for handling "
                                   "requests related to this record.")
    product_id = fields.Many2one('product.product', string='Product',
                                 help='The product associated with this record.'
                                      'This field allows you to select an '
                                      'existing product from the product '
                                      'catalog.')
    project_id = fields.Many2one('project.project', string='Project',
                                 readonly=False,
                                 related='team_id.project_id', store=True,
                                 help="The project associated with this team. "
                                      "This field is automatically filled "
                                      "based on the project assigned to "
                                      "the team.")
    priority = fields.Selection(PRIORITIES, default='1',
                                help="Set the priority level")
    stage_id = fields.Many2one('ticket.stage', string='Stage',
                               default=lambda self: self.env.ref(
                                   'odoo_website_helpdesk.stage_draft').id,
                               tracking=True,
                               group_expand='_read_group_stage_ids',
                               help="Stages of the Ticket")
    cost = fields.Float(string='Cost per hour',
                        help='The cost per hour for this record. This field '
                             'specifies the hourly cost associated with the '
                             'record, which can be used in various '
                             'calculations or reports.')
    service_product_id = fields.Many2one('product.product', string='Service '
                                                                   'Product',
                                         domain=[
                                             ('detailed_type', '=', 'service')],
                                         help="The product associated with this"
                                              "service. Only service products "
                                              "are available for selection.")
    start_date = fields.Date(string='Start Date', help="Start Date of the "
                                                       "Ticket")
    end_date = fields.Date(string='End Date', help="End Date of the Ticket")
    public_ticket = fields.Boolean(string="Public Ticket")
    invoice_ids = fields.Many2many('account.move', string='Invoices',
                                   store=True,
                                   help="To Generate Invoice based on hours "
                                        "spent on the ticket")
    task_ids = fields.Many2many('project.task', string='Tasks',
                                help="Related Task of the Ticket")
    color = fields.Integer(string="Color", default=6, help="Color")
    show_create_task = fields.Boolean(
        string="Create Task",
        default=_default_show_create_task,
        compute='_compute_show_create_task',
        help="Determines whether the 'Create Task' button should be shown "
             "for this ticket.")
    create_task = fields.Boolean(
        string="Create Task", readonly=False, related='team_id.create_task',
        store=True, help="Defines if a task should be created when this ticket "
                         "is created.")
    billable = fields.Boolean(string="Billable", default=False,
                              help="Indicates whether the ticket is billable "
                                   "or not.")

    def _compute_show_create_task(self):
        """Compute the value of the 'show_create_task' field for each record in
        the current recordset."""
        show_create_task = self._default_show_create_task()
        for record in self:
            record.show_create_task = show_create_task

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Return the stages to stage_ids"""
        stage_ids = self.env['ticket.stage'].search([])
        return stage_ids

    def action_create_invoice(self):
        """Create Invoice for Help Desk Ticket"""
        tasks = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id),
             ('ticket_id', '=', self.id)]).filtered(
            lambda line: line.ticket_billed == False)

        if not tasks:
            raise UserError('No Tasks to Bill')

        total = sum(x.effective_hours for x in tasks if x.effective_hours > 0)
        invoice_no = self.env['ir.sequence'].next_by_code(
            'ticket.invoice')
        move = self.env['account.move'].create({
            'name': invoice_no,
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'ticket_id': self.id,
            'date': fields.Date.today(),
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                {
                    'product_id': self.service_product_id.id,
                    'name': self.service_product_id.name,
                    'quantity': total,
                    'product_uom_id': self.service_product_id.uom_id.id,
                    'price_unit': self.cost if self.cost
                    else self.service_product_id.lst_price,
                    'account_id':
                        self.service_product_id.categ_id.
                        property_account_income_categ_id.id,
                }
            ],
        })
        for task in tasks:
            task.ticket_billed = True
        return {
            'view_type': 'form',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_id': False,
            'view_mode': 'form',
            'type': 'ir.actions.act_window'
        }

    def action_create_tasks(self):
        """Create Task for HelpDesk Ticket"""
        task_id = self.env['project.task'].create({
            'name': f"{self.name}-{self.subject}",
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
