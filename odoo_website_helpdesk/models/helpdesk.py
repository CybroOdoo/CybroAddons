# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High')]


class HelpDeskTicket(models.Model):
    _name = 'help.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default=lambda self: self.env['ir.sequence'].
                       next_by_code('help.ticket') or _('New'))
    customer_id = fields.Many2one('res.partner', string='customer')
    customer_name = fields.Char('Customer Name')
    subject = fields.Text('Subject', required=True)
    description = fields.Text('Description', required=True)
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    team_id = fields.Many2one('help.team', string='Helpdesk Team')
    product_id = fields.Many2one('product.product', string='Product')
    project_id = fields.Many2one('project.project', string='Project',
                                 readonly=False,
                                 related='team_id.project_id', store=True)

    priority = fields.Selection(PRIORITIES, default='1')
    stage_id = fields.Many2one('ticket.stage', string='Stage',
                               default=lambda self: self.env[
                                   'ticket.stage'].search(
                                   [('name', '=', 'Draft')], limit=1).id,
                               tracking=True,
                               group_expand='_read_group_stage_ids')

    cost = fields.Float('Cost per hour')
    service_product_id = fields.Many2one('product.product',
                                         string='Service Product',
                                         domain=[
                                             ('detailed_type', '=', 'service')])
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    public_ticket = fields.Boolean(string="Public Ticket")
    invoice_ids = fields.Many2many('account.move', string='Invoices')
    task_ids = fields.Many2many('project.task', string='Tasks')
    color = fields.Integer(string="Color", default=6)

    def _default_show_create_task(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_create_task')

    show_create_task = fields.Boolean(string="Create Task",
                                      default=_default_show_create_task,
                                      compute='_compute_show_create_task')
    create_task = fields.Boolean(string="Create Task", readonly=False,
                                 related='team_id.create_task', store=True)
    billable = fields.Boolean(string="Billable", default=False)

    def _compute_show_create_task(self):
        show_create_task = self._default_show_create_task()
        for record in self:
            record.show_create_task = show_create_task

    def default_stage_id(self):
        # Search your stage
        return self.env['ticket.stage'].search(
            [('name', '=', 'Draft')], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        return the stages to stage_ids
        """
        stage_ids = self.env['ticket.stage'].search([])
        return stage_ids

    @api.model_create_multi
    def create(self, vals_list):

        return super(HelpDeskTicket, self).create(vals_list)

    def write(self, vals):
        result = super(HelpDeskTicket, self).write(vals)
        return result

    def create_invoice(self):
        tasks = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id),
             ('ticket_id', '=', self.id)]).filtered(
            lambda line: line.ticket_billed == False)
        if not tasks:
            raise UserError('No Tasks to Bill')

        total = sum(x.effective_hours for x in tasks if x.effective_hours > 0)

        invoice_no = self.env['ir.sequence'].next_by_code(
            'ticket.invoice')
        move = self.env['account.move'].create([
            {
                'name': invoice_no,
                'move_type': 'out_invoice',
                'partner_id': self.customer_id.id,
                'ticket_id': self.id,
                'date': fields.Date.today(),
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0,
                                      {'product_id': self.service_product_id.id,
                                       'name': self.service_product_id.name,
                                       'quantity': total,
                                       'product_uom_id': self.service_product_id.uom_id.id,
                                       'price_unit': self.cost,
                                       'account_id': self.service_product_id.categ_id.property_account_income_categ_id.id,
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
            # 'view_type': 'form',
            # 'res_model': 'account.move',
            # 'res_id': move.id,
            # 'view_id': False,
            # 'view_mode': 'form',
            # 'type': 'ir.actions.act_window',
        }

    def create_tasks(self):
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

    def open_tasks(self):
        return {
            'name': 'Tasks',
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'project.task',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def open_invoices(self):
        return {
            'name': 'Invoice',
            'domain': [('ticket_id', '=', self.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }


class StageTicket(models.Model):
    _name = 'ticket.stage'
    _description = 'Ticket Stage'
    _order = 'sequence, id'

    name = fields.Char('Name')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=50)
    closing_stage = fields.Boolean('Closing Stage', default=False)
    folded = fields.Boolean('Folded in Kanban', default=False)


class Tasks(models.Model):
    _inherit = 'project.task'

    ticket_billed = fields.Boolean('Billed', default=False)


class HelpDeskTeam(models.Model):
    _name = 'help.team'
    _description = 'Helpdesk Team'

    name = fields.Char('Name')
    member_ids = fields.Many2many('res.users', string='Members')
    email = fields.Char('Email')
    project_id = fields.Many2one('project.project', string='Project')
    create_task = fields.Boolean(string="Create Task")
