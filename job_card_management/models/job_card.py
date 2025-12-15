# -*- coding: utf-8 -*-
###################################################################################
#    Job Card Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Manasa T P (<https://www.cybrosys.com>)
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
    """Create new model job card"""
    _name = "job.card"
    _description = 'Job Card'

    def _default_currency_id(self):
        """Return the default currency from the user's company."""
        return self.env.user.company_id.currency_id

    card_name = fields.Char(
        string='Job Card Name',
        required=True,
        help='The name or title of the job card.'
    )
    sequence = fields.Char(
        string='Sequence',
        readonly=True,
        help='Unique sequence number for the job card.',
        copy = False
    )
    name = fields.Char(
        string='Reference',
        help='Full reference of the job card, combining sequence and name.',
        copy=False
    )

    start_date = fields.Date(
        string='Start Date',
        required=True,
        help='The date when the job card starts.'
    )
    end_date = fields.Date(
        string='End Date',
        help='The date when the job card is expected to end.'
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        help='The project associated with this job card.'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        required=True,
        help='The user responsible for this job card.'
    )

    quality_checklist_ids = fields.Many2many(
        'quality.check.list',
        string='Quality Checklists',
        help='List of quality checklists associated with this job card.'
    )
    deadline = fields.Date(
        string='Deadline',
        help='The deadline for completing the job card.'
    )

    team_id = fields.Many2one(
        'workshop.team',
        string='Team',
        help='The team assigned to this job card.'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self._default_currency_id(),
        help='The currency used for financial calculations in this job card.'
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of the job card.'
    )

    instruction_ids = fields.One2many(
        'job.card.instruction',
        'job_card_id',
        string='Instructions',
        help='Instructions associated with this job card.'
    )
    instruction_count = fields.Integer(
        string='Instruction Count',
        default=1,
        help='Number of instructions linked to this job card.'
    )
    job_cost_sheet_ids = fields.One2many(
        'job.cost.sheet',
        'job_card_id',
        string='Cost Sheets',
        help='Cost sheets related to this job card.'
    )
    cost_sheet_amount = fields.Monetary(
        string='Total Cost',
        compute='_compute_cost_sheet_amount',
        store=True,
        help='Total cost calculated from the cost sheets.'
    )
    job_cost_sheet_untaxed_amount = fields.Monetary(
        string='Untaxed Cost',
        compute='_compute_cost_sheet_amount',
        store=True,
        help='Total untaxed cost calculated from the cost sheets.'
    )
    job_card_timesheet_ids = fields.One2many(
        'job.card.timesheet',
        'job_card_id',
        string='Timesheets',
        help='Timesheet entries for this job card.'
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submit', 'Submitted'),
            ('approve', 'Approved'),
            ('complete', 'Completed'),
            ('invoice', 'Invoiced')
        ],
        string='Status',
        default='draft',
        help='Current status of the job card.'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        help='The customer associated with this job card.'
    )
    email = fields.Char(
        string='Email',
        help='Email address for sharing this job card.'
    )
    total_hours = fields.Float(
        string='Total Working Hours',
        compute="_compute_hour",
        store=True,
        help='Total hours worked on this job card based on timesheets.'
    )
    hours = fields.Float(
        string='Remaining Hours',
        compute="_compute_hour",
        store=True,
        help='Remaining hours to complete the job card (planned hours minus worked hours).'
    )
    planned_hours = fields.Float(
        string='Planned Hours',
        required=True,
        help='Estimated hours required to complete the job card.'
    )
    mpr_count = fields.Integer(
        string='Material Requisition Count',
        compute='compute_count',
        help='Number of material requisitions linked to this job card.'
    )
    progress = fields.Float(
        string='Progress (%)',
        help='Percentage of completion based on total hours worked versus planned hours.'
    )
    invoice_name = fields.Char(
        string='Invoice Reference',
        help='Reference number of the invoice generated for this job card.'
    )
    invoice_count = fields.Integer(
        string='Invoice',
        compute='_compute_invoice_count',
        help='Number of invoices linked to this job card.'
    )

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code(
                'job.card.sequence') or '/'
        job_card = super(JobCard, self).create(vals)
        if job_card.sequence and job_card.card_name:
            job_card.name = f"{job_card.sequence}:{job_card.card_name}"
        return job_card

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

                rec.env['project.task'].create({
                    'name': rec.name,
                    'project_id': rec.project_id.id,
                    'user_ids': (4, rec.user_id.id),
                    'planned_hours': rec.planned_hours,
                    'job_card_id': rec.id
                })

    def action_completed(self):
        """ complete button """
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

    @api.constrains('start_date', 'end_date')
    def _date_constrains(self):
        """Date validation"""
        for rec in self:
            if rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(
                    _('End Date Must be greater Than Start Date...'))

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

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['account.move'].search_count([
                ('ref', '=', rec.name),
                ('move_type', '=', 'out_invoice')
            ])

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
        """calculate progress"""
        if self.planned_hours and self.total_hours:
            self.progress = round(100.0 * self.total_hours / self.planned_hours,
                                  2)
        else:
            self.progress = 0.0

    def share(self):
        """ when click on share button send mail to partner """
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
                           (rec.partner_id.name, Urls, rec.name)
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
        """compute instruction name"""
        for rec in self:
            name = rec.job_card_id.name + '/' + str(
                rec.job_card_id.instruction_count)
            if not rec.name:
                rec.job_card_id.instruction_count += 1
            rec.name = name

    job_card_id = fields.Many2one(
        'job.card',
        string='Job Card',
        help='The job card this instruction belongs to.'
    )
    name = fields.Char(
        string='Instruction Reference',
        compute='_compute_name',
        store=True,
        help='Unique reference for the instruction.'
    )
    start_date = fields.Datetime(
        string='Start Date',
        required=True,
        help='The start date and time for this instruction.'
    )
    end_date = fields.Datetime(
        string='End Date',
        help='The end date and time for this instruction.'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        required=True,
        help='The user responsible for executing this instruction.'
    )
    instruction = fields.Char(
        string='Instruction',
        required=True,
        help='Details of the instruction to be performed.'
    )
    notes = fields.Char(
        string='Notes',
        help='Additional notes or comments for this instruction.'
    )
    state = fields.Selection(
        [
            ('to_do', 'To Do'),
            ('in_progress', 'In Progress'),
            ('done', 'Done')
        ],
        string='Status',
        default='to_do',
        help='Current status of the instruction.'
    )

    @api.constrains('start_date', 'end_date')
    def _date_constrains(self):
        """Date validation"""
        for rec in self:
            if rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(
                    _('End Date Must be greater Than Start Date in Job Card Instruction..'))


class CostSheet(models.Model):
    _name = 'job.cost.sheet'
    _description = 'Cost Sheet'

    type = fields.Selection(
        [
            ('material', 'Material'),
            ('labour', 'Labour'),
            ('overhead', 'Overhead')
        ],
        string='Cost Type',
        required=True,
        help='The type of cost (material, labour, or overhead).'
    )
    job_card_id = fields.Many2one(
        'job.card',
        string='Job Card',
        help='The job card associated with this cost sheet.'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        help='The product or service related to this cost.'
    )
    quantity = fields.Float(
        string='Quantity',
        default=1,
        help='The quantity of the product or service.'
    )
    unit_price = fields.Float(
        string='Unit Price',
        help='The price per unit of the product or service.'
    )
    discount = fields.Float(
        string='Discount (%)',
        help='Discount percentage applied to the cost.'
    )
    tax = fields.Many2one(
        'account.tax',
        string='Tax',
        help='Tax applied to the cost.'
    )
    amount = fields.Float(
        string='Total Amount',
        help='Total amount including taxes after applying discount.'
    )
    untaxed_amount = fields.Float(
        string='Untaxed Amount',
        help='Total amount excluding taxes after applying discount.'
    )

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

    job_card_id = fields.Many2one(
        'job.card',
        string='Job Card',
        default=lambda self: self._default_job_card_id(),
        help='The job card this timesheet entry belongs to.'
    )
    name = fields.Char(
        string='Timesheet Name',
        store=True,
        help='Name of the timesheet entry, derived from the instruction.'
    )
    instruction_id = fields.Many2one(
        'job.card.instruction',
        string='Instruction',
        required=True,
        help='The instruction associated with this timesheet entry.'
    )
    description = fields.Char(
        string='Description',
        help='Description of the work performed in this timesheet entry.'
    )
    leader_id = fields.Many2one(
        'hr.employee',
        string='Team Leader',
        required=True,
        domain=[('workshop_position', '=', 'leader')],
        help='The team leader responsible for this timesheet entry.'
    )
    worker_id = fields.Many2one(
        'hr.employee',
        string='Worker',
        required=True,
        help='The worker who performed the task in this timesheet entry.'
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.today(),
        help='The date when the work was performed.'
    )
    time = fields.Float(
        string='Hours Worked',
        help='Number of hours worked for this timesheet entry.'
    )

    @api.onchange('instruction_id')
    def _onchange_instruction_id(self):
        """ Add instruction name """
        for rec in self:
            if rec.instruction_id:
                rec.name = rec.instruction_id.name + ':' + rec.instruction_id.instruction

    @api.model
    def create(self, vals_list):
        """ create record in account analytic line model """
        res = super(JobCardTimesheet, self).create(vals_list)
        job_card = self.env['job.card'].browse(vals_list['job_card_id'])
        task = self.env['project.task'].search(
            [('job_card_id', '=', job_card.id)])
        self.env['account.analytic.line'].create({
            'date': vals_list['date'],
            'project_id': job_card.project_id.id,
            'employee_id': vals_list['worker_id'],
            'name': vals_list['description'],
            'unit_amount': vals_list['time'],
            'task_id': task.id
        })
        return res
