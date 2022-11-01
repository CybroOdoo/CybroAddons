# -*- coding: utf-8 -*-
###################################################################################
#    Job Card
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from werkzeug import urls

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class JobCard(models.Model):
    _name = "job.card"
    _description = 'Job Cards'

    def _default_currency_id(self):
        """get currency id"""
        return self.env.user.company_id.currency_id

    card_name = fields.Char('Name', required=True, store=True)
    sequence = fields.Char('Name', store=True)
    name = fields.Char('Name', store=True)

    start_date = fields.Date('Starting Date', required=True)
    end_date = fields.Date('Ending Date', required=False)
    project_id = fields.Many2one('project.project', required=True)
    user_id = fields.Many2one('res.users', string='Assigned To', required=True)

    quality_checklist_id = fields.Many2many('quality.check.list')
    deadline = fields.Date()

    team_id = fields.Many2one('workshop.team')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, default=lambda
            self: self._default_currency_id())
    description = fields.Text('Description')

    instruction_ids = fields.One2many('job.card.instruction', 'job_card_id')
    instruction_count = fields.Integer(default=1)
    job_cost_sheet_ids = fields.One2many('job.cost.sheet', 'job_card_id')
    cost_sheet_amount = fields.Monetary(compute='_compute_cost_sheet_amount',
                                        store=True)
    job_cost_sheet_untaxed_amount = fields.Monetary(
        compute='_compute_cost_sheet_amount', store=True)
    job_card_timesheet_ids = fields.One2many('job.card.timesheet',
                                             'job_card_id')
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submitted'), ('approve', 'Approved'),
         ('complete', 'Completed'), ('invoice', 'Invoiced')], default='draft')
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 required=True)
    email = fields.Char('Mail', help="for share this job card")
    total_hours = fields.Float('Total Working Hour', store=True,
                               compute="_compute_hour")
    hours = fields.Float('Total working hour', store=True,
                         compute="_compute_hour")
    planned_hours = fields.Float('Planned Hours', required=True,
                                 help="Planned hour for this task")
    mpr_count = fields.Integer(compute='compute_count')
    progress = fields.Float(help="progress of this task")
    invoice_name = fields.Char('Name', help="reference of invoice")

    def action_submit(self):
        """submit"""
        for rec in self:
            if not rec.instruction_ids.ids:
                raise ValidationError(
                    'You cant submit the job card without instruction lines')
            else:
                rec.state = 'submit'

    def action_approve(self):
        """approve, Creating task"""
        for rec in self:
            if not rec.job_cost_sheet_ids.ids:
                raise ValidationError(
                    'You cant approve the job card without Cost sheet information')
            else:
                rec.state = 'approve'

                task = rec.env['project.task'].create({
                    'name': rec.name,
                    'project_id': rec.project_id.id,
                    'user_ids': (4, rec.user_id.id),
                    'planned_hours': rec.planned_hours,
                    'job_card_id': rec.id
                })

    def action_completed(self):
        for rec in self:
            rec.state = 'complete'

    @api.depends('job_card_timesheet_ids.time')
    def _compute_hour(self):
        """calculate time cost amount"""
        for rec in self:
            rec.cost_sheet_amount = sum(
                rec.job_card_timesheet_ids.mapped('time'))
            rec.total_hours = sum(
                rec.job_card_timesheet_ids.mapped('time'))
            rec.hours = rec.planned_hours - rec.total_hours

    @api.depends('job_cost_sheet_ids.amount')
    def _compute_cost_sheet_amount(self):
        """calculate time cost amount"""
        for rec in self:
            rec.cost_sheet_amount = sum(rec.job_cost_sheet_ids.mapped('amount'))
            rec.job_cost_sheet_untaxed_amount = sum(
                rec.job_cost_sheet_ids.mapped('untaxed_amount'))

    @api.onchange('card_name', 'sequence')
    def _onchange_card_name(self):
        """create the sequence"""
        for rec in self:
            if not self.sequence:
                sequence_code = 'job.card.sequence'
                self.sequence = self.env['ir.sequence'].next_by_code(
                    sequence_code)

            if rec.card_name and rec.sequence:
                self.name = self.sequence + ':' + self.card_name

    @api.onchange('job_card_timesheet_ids.time')
    def _onchange_time(self):
        for rec in self:
            rec.hours = sum(rec.job_cost_sheet_ids.mapped('time'))
            rec.days = rec.hours / 60

    def create_pmr(self):
        """create purchase material request"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'PMR',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'material.requisition',
            'context': {
                'default_job_card_id': self.id
            }

        }

    def get_pmr(self):
        """create purchase material request"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'PMR',
            'view_mode': 'tree,form',
            'res_model': 'material.requisition',
            'domain': [('job_card_id', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.depends('name')
    def compute_count(self):
        """Compute mr count"""
        for rec in self:
            if rec.env['material.requisition'].search(
                    [('job_card_id', '=', rec.id)]):
                rec.mpr_count = rec.env['material.requisition'].search_count(
                    [('job_card_id', '=', rec.id)])
            else:
                rec.mpr_count = 0

    def create_invoice(self):
        """Create invoice"""
        lines = []
        for rec in self:
            if rec.job_cost_sheet_ids:
                for job in rec.job_cost_sheet_ids:
                    value = (0, 0, {
                        'product_id': job.product_id.id,
                        'price_unit': job.amount,
                        'quantity': job.quantity,
                    })
                    lines.append(value)
                invoice_line = {
                    'move_type': 'out_invoice',
                    'partner_id': rec.partner_id.id,
                    'invoice_user_id': rec.env.user.id,
                    'invoice_origin': rec.name,
                    'ref': rec.name,
                    'invoice_line_ids': lines,
                }
                inv = self.env['account.move'].create(invoice_line)
                rec.state = 'invoice'
                rec.invoice_name = inv.name

    def get_invoice(self):
        """View the invoice"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('ref', '=', self.name)],
            'context': "{'create': False}"
        }

    @api.onchange('planned_hours', 'total_hours')
    def _onchange_progress(self):
        if self.planned_hours and self.total_hours:
            self.progress = round(100.0 * self.total_hours / self.planned_hours,
                                  2)
        else:
            self.progress = 0.0

    def share(self):
        for rec in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'web#id=%(id)s&model=job.card&view_type=form' % {
                                     'id': self.id})

            mail_content = _('Hi %s,<br>'
                             'Job Card'
                             '<div style = "text-align: center; margin-top: 16px;"><a href = "%s"'
                             'style = "padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; '
                             'border-color:#875A7B;text-decoration: none; display: inline-block; '
                             'margin-bottom: 0px; font-weight: 400;text-align: center; vertical-align: middle; '
                             'cursor: pointer; white-space: nowrap; background-image: none; '
                             'background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px;">'
                             'View %s</a></div>'
                             ) % \
                           (rec.name, Urls, rec.name)
            main_content = {
                'subject': _('Job Card: %s') % self.name,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': rec.partner_id.email
            }

            mail_id = self.env['mail.mail'].create(main_content)
            mail_id.mail_message_id.body = mail_content
            mail_id.send()


class JobCardInstruction(models.Model):
    _name = "job.card.instruction"
    _description = 'Job Cards Instruction'
    _rec_name = 'instruction'

    @api.depends('job_card_id')
    def _compute_name(self):
        for rec in self:
            name = rec.job_card_id.name + '/' + str(
                rec.job_card_id.instruction_count)
            if not rec.name:
                rec.job_card_id.instruction_count += 1
            rec.name = name

    job_card_id = fields.Many2one('job.card')
    name = fields.Char('Name', compute='_compute_name', store=True)
    start_date = fields.Datetime('Starting Date', required=True)
    end_date = fields.Datetime('Ending Date', required=False)
    user_id = fields.Many2one('res.users', string='Assigned To', required=True)
    instruction = fields.Char(help='Instructions', required=True)
    notes = fields.Char(help='notes for this instruction')
    state = fields.Selection(
        [('to_do', 'To Do'), ('in_progress', 'In progress'), ('done', 'Done')],
        default='to_do')


class CostSheet(models.Model):
    _name = 'job.cost.sheet'
    _description = 'Cost Sheet'

    type = fields.Selection([('material', 'Material'), ('labour', 'Labour'),
                             ('overhead', 'Overhead')], required=True,
                            help='Type of product')
    job_card_id = fields.Many2one('job.card')
    product_id = fields.Many2one('product.product', required=True)
    quantity = fields.Float('Quantity', default=1)
    unit_price = fields.Float('Unit Price')
    discount = fields.Float('Discount %')
    tax = fields.Many2one('account.tax')
    amount = fields.Float('Amount')
    untaxed_amount = fields.Float('Untaxed Amount')

    @api.onchange('product_id', 'discount', 'tax')
    def _onchange_product_id(self):
        """calculate the amount"""
        for rec in self:
            rec.unit_price = rec.product_id.list_price
            rec.amount = rec.unit_price * rec.quantity
            rec.untaxed_amount = rec.unit_price * rec.quantity
            if rec.tax:
                taxes = rec.tax.compute_all(**rec._prepare_compute_all_values())
                rec.amount = taxes['total_included']
                rec.untaxed_amount = taxes['total_excluded']
            if rec.discount:
                rec.amount = rec.amount - (rec.amount * rec.discount / 100)
                rec.untaxed_amount = rec.untaxed_amount - (
                        rec.untaxed_amount * rec.discount / 100)

    def _prepare_compute_all_values(self):
        """prepare values"""
        self.ensure_one()
        return {
            'price_unit': self.unit_price,
            'currency': self.job_card_id.currency_id,
            'quantity': self.quantity,
            'product': self.product_id,
            'partner': self.job_card_id.user_id.partner_id,
        }


class JobCardTimesheet(models.Model):
    _name = 'job.card.timesheet'
    _description = 'Job Card TimeSheet'

    job_card_id = fields.Many2one('job.card', default=lambda
        self: self._default_job_card_id())
    name = fields.Char('Instruction Name', store=True)
    instruction_id = fields.Many2one('job.card.instruction', required=True, )
    description = fields.Char('Description')
    leader_id = fields.Many2one('hr.employee', required=True,
                                domain=[('workshop_position', '=', 'leader')],
                                help="leader for this instruction")
    worker_id = fields.Many2one('hr.employee', required=True,
                                help="workers for this instruction",
                                string="Workers")
    date = fields.Date('Date', default=fields.Date.today())
    time = fields.Float('Time')

    @api.onchange('instruction_id')
    def _onchange_instruction_id(self):
        for rec in self:
            if rec.instruction_id:
                rec.name = rec.instruction_id.name + ':' + rec.instruction_id.instruction

    @api.model
    def create(self, vals_list):
        res = super(JobCardTimesheet, self).create(vals_list)
        job_card = self.env['job.card'].browse(vals_list['job_card_id'])
        task = self.env['project.task'].search(
            [('job_card_id', '=', job_card.id)])
        attendance = self.env['account.analytic.line'].create({
            'date': vals_list['date'],
            'project_id': job_card.project_id.id,
            'employee_id': vals_list['worker_id'],
            'name': vals_list['description'],
            'unit_amount': vals_list['time'],
            'task_id': task.id
        })
        return res
