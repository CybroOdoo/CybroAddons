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


class HelpDeskTicket(models.Model):
    _name = 'help.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default=lambda self: self.env['ir.sequence'].
                       next_by_code('help.ticket') or _('New'))
    customer_id = fields.Many2one('res.partner', string='Customer Name')
    customer_name = fields.Char('Customer Name')
    subject = fields.Text('Subject', required=True)
    description = fields.Text('Description', required=True)
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    team_id = fields.Many2one('help.team', string='Helpdesk Team')
    product_id = fields.Many2many('product.template', string='Product')
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
    user_id = fields.Many2one('res.users',
                              default=lambda self: self.env.user,
                              check_company=True,
                              index=True, tracking=True)
    cost = fields.Float('Cost per hour')
    service_product_id = fields.Many2one('product.product',
                                         string='Service Product',
                                         domain=[
                                             ('detailed_type', '=', 'service')])
    create_date = fields.Datetime('Creation Date')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    public_ticket = fields.Boolean(string="Public Ticket")
    invoice_ids = fields.Many2many('account.move', string='Invoices')
    task_ids = fields.Many2many('project.task', string='Tasks')
    color = fields.Integer(string="Color")
    replied_date = fields.Datetime('Replied date')
    last_update_date = fields.Datetime('Last Update Date')
    ticket_type = fields.Many2one('helpdesk.types', string='Ticket Type')
    team_head = fields.Many2one('res.users', string='Team Leader',
                                compute='_compute_team_head')
    assigned_user = fields.Many2one('res.users',
                                    domain=lambda self: [
                                        ('groups_id', 'in', self.env.ref(
                                            'odoo_website_helpdesk.helpdesk_user').id)])
    category_id = fields.Many2one('helpdesk.categories')
    tags = fields.Many2many('helpdesk.tag')
    assign_user = fields.Boolean(default=False)
    attachment_ids = fields.One2many('ir.attachment', 'res_id')

    @api.onchange('team_id', 'team_head')
    def team_leader_domain(self):
        li = []
        for rec in self.team_id.member_ids:
            li.append(rec.id)
        return {'domain': {'assigned_user': [('id', 'in', li)]}}

    @api.depends('team_id')
    def _compute_team_head(self):
        self.team_head = self.team_id.team_lead_id.id

    @api.onchange('stage_id')
    def mail_snd(self):
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
        if self.team_id:
            self.team_head = self.team_id.team_lead_id.id
            mail_template = self.env.ref(
                'odoo_website_helpdesk.odoo_website_helpdesk_assign')
            mail_template.sudo().write({
                'email_to': self.team_head.email,
                'subject': self.name
            })
            mail_template.sudo().send_mail(self.id, force_send=True)
        else:
            raise ValidationError("Please choose a Helpdesk Team")

    def _default_show_create_task(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_create_task')

    show_create_task = fields.Boolean(string="Create Task",
                                      default=_default_show_create_task,
                                      compute='_compute_show_create_task')
    create_task = fields.Boolean(string="Create Task", readonly=False,
                                 related='team_id.create_task', store=True)
    billable = fields.Boolean(string="Billable", default=False)

    def _default_show_category(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.show_category')

    show_category = fields.Boolean(default=_default_show_category,
                                   compute='_compute_show_category')
    customer_rating = fields.Selection(RATING, default='0', readonly=True)

    review = fields.Char('Review', readonly=True)
    kanban_state = fields.Selection([
        ('normal', 'Ready'),
        ('done', 'In Progress'),
        ('blocked', 'Blocked'), ], default='normal')

    def _compute_show_category(self):
        show_category = self._default_show_category()
        for rec in self:
            rec.show_category = show_category

    def _compute_show_create_task(self):
        show_create_task = self._default_show_create_task()
        for record in self:
            record.show_create_task = show_create_task

    def auto_close_ticket(self):
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

    def action_send_reply(self):
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


class StageTicket(models.Model):
    _name = 'ticket.stage'
    _description = 'Ticket Stage'
    _order = 'sequence, id'
    _fold_name = 'fold'

    name = fields.Char('Name')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=50)
    closing_stage = fields.Boolean('Closing Stage', default=False)
    cancel_stage = fields.Boolean('Cancel Stage', default=False)
    starting_stage = fields.Boolean('Start Stage', default=False)
    folded = fields.Boolean('Folded in Kanban', default=False)
    template_id = fields.Many2one('mail.template',
                                  domain="[('model', '=', 'help.ticket')]")
    group_ids = fields.Many2many('res.groups')
    fold = fields.Boolean(string='Fold')

    def unlink(self):
        for rec in self:
            tickets = rec.search([])
            sequence = tickets.mapped('sequence')
            lowest_sequence = tickets.filtered(
                lambda x: x.sequence == min(sequence))
            if self.name == "Draft":
                raise UserError(_("Cannot Delete This Stage"))
            if rec == lowest_sequence:
                raise UserError(_("Cannot Delete '%s'" % (rec.name)))
            else:
                res = super().unlink()
                return res


class HelpdeskTypes(models.Model):
    _name = 'helpdesk.types'
    _description = 'Helpdesk Types'

    name = fields.Char(string='Type')


class Tasks(models.Model):
    _inherit = 'project.task'

    ticket_billed = fields.Boolean('Billed', default=False)


class HelpdeskTags(models.Model):
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tags'

    name = fields.Char(string='Tag')
