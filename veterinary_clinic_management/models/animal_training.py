# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AnimalTraining(models.Model):
    """
    Model for storing training details in veterinary clinic management.
    """
    _name = 'animal.training'
    _inherit = 'mail.thread'
    _rec_name = 'training_no'
    _description = 'Animal Training'

    training_no = fields.Char(
        string="Training No",
        default=lambda self: _('New'),
        copy=False,
        readonly=True,
        tracking=True,
        help="Unique identifier for the training appointment",
    )
    appointment_date = fields.Date(
        string="Appointment Date",
        default=fields.Date.today,
        copy="False",
        help="Date and time of the training appointment",
    )
    closed_date = fields.Date(
        string="Closed Date",
        help="Close date of the appointment"
    )
    training_emp_id = fields.Many2one(
        string="Training Employee",
        comodel_name="res.partner",
        copy="False",
        help="Employee responsible for the training",
    )
    animal_id = fields.Many2one(
        string="Animal",
        comodel_name="res.patient",
        help="Animal undergoing training",
    )
    animal_type_id = fields.Many2one(
        string="Animal Type",
        comodel_name="animal.types",
        related="animal_id.pet_type_id",
        readonly=True,
        help="Type of animal undergoing training",
    )
    breed_id = fields.Many2one(
        string="Breed",
        comodel_name="breed.types",
        related="animal_id.breed_id",
        readonly=True,
        help="Breed of the animal undergoing training",
    )
    package_id = fields.Many2one(
        string="Package",
        comodel_name="training.package",
        help="Training package chosen for the animal",
    )
    package_duration = fields.Integer(
        string="Package Duration",
        related="package_id.days",
        help="Duration of the training package in days",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id.id,
        help="Currency used for pricing",
    )
    charge = fields.Monetary(
        string="Charge",
        related="package_id.charge",
        help="Cost charged for the training package",
    )
    start_date = fields.Date(
        string="Start Date",
        copy="False",
        help="Date when the training started",
    )
    end_date = fields.Date(
        string="End Date",
        copy="False",
        help="Date when the training ended",
    )
    signature = fields.Binary(
        string="Signature",
        help="Digital signature acknowledging the training completion",
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('in-consultation', 'In-Consultation'),
         ('close', 'Close'),
         ('cancel', 'Cancel')],
        default="draft",
        help="Current state of the training appointment",
        tracking=True,
    )
    training_invoice_id = fields.Many2one(
        string="Invoice",
        comodel_name='account.move',
        readonly=True,
        copy="False",
        help="Invoice generated for the training appointment",
    )
    is_invoice = fields.Boolean(
        help="Flag indicating whether an invoice has been generated for the training",
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_count",
        help="Number of invoices associated with this training",
    )
    payment_ribbon = fields.Char(
        compute='_compute_payment_ribbon',
        help="Payment status of the training invoice",
    )

    def _compute_invoice_count(self):
        """Compute the number of invoices associated with the training."""
        for rec in self:
            rec.invoice_count = len(rec.training_invoice_id)

    @api.depends('training_invoice_id')
    def _compute_payment_ribbon(self):
        """Compute the payment status badge based on the training invoice."""
        for record in self:
            record.payment_ribbon = record.training_invoice_id.payment_state

    @api.onchange('appointment_date')
    def _onchange_appointment_date(self):
        """
          Validate the appointment date to ensure it is not set before the current date.

          This method is triggered when the 'appointment_date' field is changed.
          It raises a ValidationError if the selected appointment date is earlier
          than the current date and time.
                    """
        if self.appointment_date < fields.Date.today():
            raise ValidationError(
                "Selected appointment date cannot be before today's date.")

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to assign a unique training appointment number."""
        for vals in vals_list:
            if vals.get('training_no', 'New') == 'New':
                vals['training_no'] = self.env['ir.sequence'].next_by_code('training.sequence') or 'New'
        return super().create(vals_list)

    def action_create_invoice(self):
        """Create an invoice for the training appointment."""
        for record in self:
            product = self.env['product.product'].search([('name', '=', 'Training')], limit=1)
            invoice = self.env['account.move'].create([
                {
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.context_today(self),
                    'partner_id': self.animal_id.owner_name_id.id,
                    'currency_id': self.currency_id.id,
                    'training_bill_invoice_id': self.id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'name': product.name,
                        'price_unit': record.charge,
                    })]
                }])
            self.training_invoice_id = invoice.id
            self.is_invoice = True
            return {
                'name': 'Customer Invoices',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'context': {'default_move_type': 'out_invoice'},
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': invoice.id

            }

    def action_view_invoice(self):
        """Action to view the invoice associated with the training appointment."""
        return {
            'name': 'Customer Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.training_invoice_id.id
        }
