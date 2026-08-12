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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Defines the Medicare Appointment model for handling patient bookings."""

from markupsafe import Markup
from odoo import models, fields, api


class MedicareAppointment(models.Model):
    """Model for patient appointment requests, integrating with mail thread for communication."""
    _name = 'medicare.appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Medicare Appointment'
    _order = 'date desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: 'New',
                       tracking=True)
    patient_name = fields.Char(string='Patient Name', required=True, tracking=True)
    phone = fields.Char(string='Phone Number', required=True, tracking=True)
    email = fields.Char(string='Email', tracking=True)
    date = fields.Date(string='Requested Date', required=True, tracking=True)
    department_id = fields.Many2one('medicare.department', string='Department', tracking=True)
    doctor_id = fields.Many2one('medicare.doctor', string='Doctor', tracking=True)
    state = fields.Selection([
        ('draft', 'New Request'),
        ('confirmed', 'Confirmed'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Additional Notes')

    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Char(string='Gender')
    appointment_type = fields.Char(string='Appointment Type')
    visit_mode = fields.Char(string='Visit Mode')
    preferred_time = fields.Char(string='Preferred Time')

    chief_complaint = fields.Text(string='Chief Complaint')
    insurance_provider = fields.Char(string='Insurance Provider')
    insurance_id = fields.Char(string='Insurance ID')
    current_medications = fields.Text(string='Current Medications')

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to assign a sequence number and send a confirmation email."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('medicare.appointment') or 'New'
        records = super(MedicareAppointment, self).create(vals_list)
        for record in records:
            if record.email:
                body = Markup(f"""
                    <p>Dear {record.patient_name},</p>
                    <p>Your appointment request has been successfully received.</p>
                    <ul>
                        <li><strong>Reference:</strong> {record.name}</li>
                        <li><strong>Date:</strong> {record.date}</li>
                        <li><strong>Department:</strong> {record.department_id.name if record.department_id else 'General'}</li>
                        <li><strong>Doctor:</strong> {record.doctor_id.name if record.doctor_id else 'Any Available Doctor'}</li>
                    </ul>
                    <p>We will contact you shortly to confirm your schedule.</p>
                    <br/>
                    <p>Thank you,<br/>MediCare Team</p>
                """)
                record.message_post(
                    body=body,
                    subject="Appointment Confirmation Sent",
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                )

                self.env['mail.mail'].sudo().create({
                    'subject': f'Appointment Confirmation - {record.name}',
                    'body_html': body,
                    'email_to': record.email,
                    'auto_delete': True,
                }).send()
        return records

    def action_confirm(self):
        """Transition the appointment state to 'confirmed'."""
        for rec in self:
            rec.state = 'confirmed'

    def action_done(self):
        """Transition the appointment state to 'done'."""
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        """Transition the appointment state to 'cancelled'."""
        for rec in self:
            rec.state = 'cancelled'

    def action_draft(self):
        """Transition the appointment state to 'draft'."""
        for rec in self:
            rec.state = 'draft'
