# -*- coding: utf-8 -*-
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
from odoo import _, api, fields, models, Command
from odoo.exceptions import ValidationError


class ClassType(models.Model):
    """Class is used to create the music class records."""
    _name = 'class.type'
    _description = 'Class Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(help='Class name.', required=True)
    from_date = fields.Date(string='From', help='Class starting date.',
                            required=True)
    to_date = fields.Date(string='To', help='Class ending date.',
                          required=True)
    duration = fields.Integer(string='Duration', compute='_compute_duration',
                              store=True, help='Duration of the class.')
    service_id = fields.Many2one('service.type', string='Services',
                                 help='Type of service.')
    instrument_id = fields.Many2one('product.product',
                                    string='Instrument',
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
                                 string='Class Lessons',
                                 help='Daily class lessons records.')
    student_ids = fields.Many2many('res.partner', string='Student',
                                   domain=[('student', '=', True)],
                                   help='Student who joined in the class.',
                                   required=True)
    order_count = fields.Integer(compute='_compute_order_count',
                                 string='Order Count',
                                 help='Total count of the invoice.')
    sunday = fields.Boolean(string='Sunday',
                            help='Mark the day as a workday.')
    monday = fields.Boolean(string='Monday',
                            help='Mark the day as a workday.')
    tuesday = fields.Boolean(string='Tuesday',
                             help='Mark the day as a workday.')
    wednesday = fields.Boolean(string='Wednesday',
                               help='Mark the day as a workday.')
    thursday = fields.Boolean(string='Thursday',
                              help='Mark the day as a workday.')
    friday = fields.Boolean(string='Friday',
                            help='Mark the day as a workday.')
    saturday = fields.Boolean(string='Saturday',
                              help='Mark the day as a workday.')
    company_id = fields.Many2one(
        'res.company', string='Company', copy=False, readonly=True,
        help="Current company",
        default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.student_ids:
                record.student_ids.filtered(
                    lambda s: not s.class_id
                ).write({'class_id': record.id})
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'student_ids' in vals:
            for record in self:
                record.student_ids.filtered(
                    lambda s: not s.class_id
                ).write({'class_id': record.id})
        return res

    @api.depends('from_date', 'to_date', 'repeats', 'monday', 'tuesday',
                 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    def _compute_duration(self):
        """Compute the working days between the from and to date."""
        for records in self:
            if records.from_date and records.to_date:
                workdays = []
                if records.repeats == 'weekly':
                    days_map = {
                        0: records.monday,
                        1: records.tuesday,
                        2: records.wednesday,
                        3: records.thursday,
                        4: records.friday,
                        5: records.saturday,
                        6: records.sunday,
                    }
                    workdays = [
                        day for day, checked in days_map.items() if checked
                    ]
                if not workdays:
                    workdays = [0, 1, 2, 3, 4]  # Monday-Friday default

                num_work_days = 0
                current_date = records.from_date
                while current_date <= records.to_date:
                    if current_date.weekday() in workdays:
                        num_work_days += 1
                    current_date += timedelta(days=1)
                records.duration = num_work_days
            else:
                records.duration = 0

    def _compute_order_count(self):
        """Compute the total count of the related invoices."""
        for record in self:
            record.order_count = self.env['account.move'].search_count([
                ('partner_id', 'in', record.student_ids.ids),
                ('class_id', '=', record.id),
            ])

    @api.constrains('from_date', 'to_date')
    def _check_from_and_to_date(self):
        for record in self:
            if record.from_date and record.to_date and (
                record.from_date > record.to_date
            ):
                raise ValidationError(
                    _('From Date must be earlier than To Date.')
                )

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
        """Button to create the invoice for students."""
        for record in self:
            if not record.instrument_id:
                raise ValidationError(_(
                    'Please select an Instrument before creating an invoice.'
                ))
            for student in record.student_ids:
                existing_invoice = self.env['account.move'].search([
                    ('partner_id', '=', student.id),
                    ('class_id', '=', record.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '!=', 'cancel'),
                ], limit=1)
                if not existing_invoice:
                    self.env['account.move'].create([{
                        'move_type': 'out_invoice',
                        'partner_id': student.id,
                        'class_id': record.id,
                        'invoice_date': record.from_date,
                        'invoice_line_ids': [Command.create({
                            'product_id': record.instrument_id.id,
                            'price_unit': record.instrument_id.lst_price,
                            'quantity': record.duration or 1,
                        })],
                    }])
            record.write({'state': 'invoice'})

    def related_order(self):
        """Related invoice in smart button."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [
                ('partner_id', 'in', self.student_ids.ids),
                ('class_id', '=', self.id),
            ],
            'context': {'create': False},
        }
