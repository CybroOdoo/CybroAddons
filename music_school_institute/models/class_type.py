# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class ClassType(models.Model):
    """Class is used to create the music class records."""
    _name = 'class.type'
    _description = 'Class Type'

    name = fields.Char(string='Name', help='Class name.', required=True)
    from_date = fields.Date(string='From', help='Class starting date.',
                            required=True)
    to_date = fields.Date(string='To', help='Class ending date.', required=True)
    service_id = fields.Many2one('service.type', string='Services',
                                 help='Type of service.')
    instrument_id = fields.Many2one('product.product',
                                    String='Instrument',
                                    domain=[('music_instrument', '=', True)],
                                    required=True,
                                    help='Instrument used in the music class.')
    teacher_id = fields.Many2one('hr.employee', string='Teacher',
                                 domain=[('teacher', '=', True)],
                                 required=True,
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
    lesson_ids = fields.One2many('class.lesson.type',
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
                                 default=lambda self: self.env.company.id)

    @api.constrains('to_date', 'from_date')
    def date_constrains(self):
        """Validation for date fields"""
        for rec in self:
            if rec.to_date < rec.from_date:
                raise ValidationError(
                    _('Sorry, To Date Must be greater Than From Date...'))

    def _compute_duration(self):
        """Function used to compute the days between the from and to date."""
        for records in self:
            if records.from_date and records.to_date:
                true_days = []
                daily_hours = sum(int(rec.hours) for rec in records.lesson_ids)
                if records.repeats == 'weekly':
                    if records.sunday:
                        true_days.append('Sunday')
                    if records.monday:
                        true_days.append('Monday')
                    if records.tuesday:
                        true_days.append('Tuesday')
                    if records.wednesday:
                        true_days.append('Wednesday')
                    if records.thursday:
                        true_days.append('Thursday')
                    if records.friday:
                        true_days.append('Friday')
                    if records.saturday:
                        true_days.append('Saturday')
                    return len(true_days) * daily_hours
                elif records.repeats == 'monthly':
                    delta = relativedelta(records.to_date, records.from_date)
                    months_difference = delta.years * 12 + delta.months
                    return int(months_difference) * daily_hours
                else:
                    return daily_hours

    def action_button_class_start(self):
        """Change the corresponding class state to start."""
        self.write({'state': 'started'})

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
                 'music_class_id': self.id,
                 'invoice_line_ids': [(0, 0, {
                     'product_id': self.instrument_id.id,
                     'price_unit': self.instrument_id.lst_price,
                     'quantity': int(self._compute_duration())})]}])
        self.write({'state': 'invoice'})

    def related_order(self):
        """Related invoice in smart button."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('music_class_id', '=', self.id)],
            'context': {'create': False}}

    def _compute_order_count(self):
        """To compute the total count of the invoice."""
        for record in self:
            record.order_count = self.env['account.move'].search_count(
                [('music_class_id', '=', self.id)])
