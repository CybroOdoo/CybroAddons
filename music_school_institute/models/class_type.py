# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P (<https://www.cybrosys.com>)
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
from datetime import timedelta
from odoo import api, fields, models


class ClassType(models.Model):
    """Class is used to create the music class records."""
    _name = 'class.type'
    _description = 'Class Type'

    name = fields.Char(string='Name', help='Class name.', required=True)
    from_date = fields.Date(string='From', help='Class starting date.',
                            required=True)
    to_date = fields.Date(string='To', help='Class ending date.', required=True)
    duration = fields.Integer(string='Duration', compute='_compute_duration',
                              store=True, help='Duration of the class.')
    service_id = fields.Many2one('service.type', string='Services',
                                 help='Type of service.')
    instrument_id = fields.Many2one('product.product',
                                    String='Instrument',
                                    domain=[('music_instrument', '=', True)],
                                    help='Instrument used in the music class.')
    teacher_id = fields.Many2one('hr.employee', string='Teacher',
                                 domain=[('teacher', '=', True)],
                                 help='Teacher name.')
    location = fields.Char(string='Location', help='Location of the class.')
    repeats = fields.Selection(selection=[('weekly', 'Weekly'),
                                          ('monthly', 'Monthly')],
                               string='Repeats',
                               help='Repeated days per week.')
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('started', 'Started'),
                   ('completed', 'Completed'),
                   ('invoice', 'Invoiced'), ('canceled', 'Canceled')],
        default='draft', help='State of the class.')
    lesson_ids = fields.One2many('class.lesson',
                                 'relation_id',
                                 String='Class Lessons',
                                 help='Daily class lessons records.')
    student_ids = fields.Many2many('res.partner', string='Student',
                                   domain=[('student', '=', True)],
                                   String='Student ID',
                                   help='Student who joined in the class.',
                                   required=True)
    order_count = fields.Integer(compute='_compute_order_count',
                                 String='Order Count',
                                 help='Total count of the invoice.')
    sunday = fields.Boolean(string='Sunday', help='Mark the day as a workday.')
    monday = fields.Boolean(string='Monday', help='Mark the day as a workday.')
    tuesday = fields.Boolean(string='Tuesday',
                             help='Mark the day as a workday.')
    wednesday = fields.Boolean(string='Wednesday',
                               help='Mark the day as a workday.')
    thursday = fields.Boolean(string='Thursday',
                              help='Mark the day as a workday.')
    friday = fields.Boolean(string='Friday', help='Mark the day as a workday.')
    saturday = fields.Boolean(string='Saturday',
                              help='Mark the day as a workday.')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    @api.depends('from_date', 'to_date')
    def _compute_duration(self):
        """Function used to compute the days between the from and to date."""
        for records in self:
            if records.from_date and records.to_date:
                num_work_days = 0
                current_date = records.from_date
                while current_date <= records.to_date:
                    if current_date.weekday() < 5:
                        num_work_days += 1
                    current_date += timedelta(days=1)
                self.duration = num_work_days

    def action_button_class_start(self):
        """Change the corresponding class state to start."""
        self.write({'state': 'started'})
        return self._compute_duration()

    def action_button_set_to_draft(self):
        """Change the corresponding class state to draft."""
        self.write({'state': 'draft'})

    def action_button_class_cancel(self):
        """Change the corresponding class state to cancel."""
        self.write({'state': 'canceled'})

    def action_button_class_completed(self):
        """Change the corresponding class state to complete."""
        self.write({'state': 'completed'})

    def action_button_create_order(self):
        """Button to create the invoice."""
        for student in self.student_ids:
            self.env['account.move'].create([
                {'move_type': 'out_invoice',
                 'partner_id': student.id,
                 'invoice_date': self.from_date,
                 'invoice_line_ids': [(0, 0, {
                     'product_id': self.instrument_id.id,
                     'price_unit': self.instrument_id.lst_price,
                     'quantity': self.duration})]}])
        self.write({'state': 'invoice'})

    def related_order(self):
        """Related invoice in smart button."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('partner_id', 'in', self.student_ids.ids)],
            'context': {'create': False}}

    def _compute_order_count(self):
        """To compute the total count of the invoice."""
        for record in self:
            record.order_count = self.env['account.move'].search_count(
                [('partner_id', 'in', self.student_ids.ids)])
