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
from collections import Counter
from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError


class AnimalGrooming(models.Model):
    """Model for storing Grooming details in veterinary Clinic Management"""
    _name = 'animal.grooming'
    _inherit = 'mail.thread'
    _rec_name = 'grooming_no'
    _description = 'Animal Grooming'

    grooming_no = fields.Char(string="Case No", default=lambda self: _('New'),
                              copy=False, readonly=True, tracking=True,
                              help="Unique identifier for the grooming case")
    appointment_date = fields.Date(string="Appointment Date", default=fields.Date.today,
                                   copy="False",
                                   help="Date and time of the grooming appointment")
    closed_date = fields.Date(
        string="Closed Date",
        copy="False",
        help="Close date of the appointment"
    )
    patient_name_id = fields.Many2one(string="Animal", comodel_name="res.patient",
                                      help="Patient (Animal) associated with this grooming case")
    grooming_employee_id = fields.Many2one(string="Grooming Employee", comodel_name="res.partner", copy="False",
                                           help="Employee responsible for grooming the animal")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in-consultation', 'In Consultation'),
        ('close', 'Close'),
        ('cancel', 'Cancel'),
    ], default="draft", help="State of the grooming case", tracking=True)
    grooming_line_ids = fields.One2many('grooming.service.line', 'grooming_id',
                                        string="Grooming Services",
                                        help="Services provided during the grooming session")
    currency_id = fields.Many2one(comodel_name="res.currency",
                                  default=lambda self: self.env.company.currency_id.id,
                                  help="Currency used for the grooming invoice")
    grooming_total = fields.Monetary(compute="_compute_grooming_total", string='Total',
                                     help="Total cost of all grooming services provided")
    grooming_invoice_id = fields.Many2one(string="Invoice", comodel_name='account.move',
                                          readonly=True,
                                          copy="False",
                                          help="Invoice associated with the grooming case")
    is_invoice = fields.Boolean(string="Has Invoice",
                                help="Whether an invoice has been created for this grooming case")
    invoice_count = fields.Integer(compute="_compute_invoice_count",
                                   help="Number of invoices associated with this grooming case")
    payment_ribbon = fields.Char(compute='_compute_payment_ribbon',
                                 help="Ribbon or badge indicating payment status")

    @api.depends('grooming_line_ids.price')
    def _compute_grooming_total(self):
        """Compute the total cost of grooming services."""
        for record in self:
            record.grooming_total = sum(record.grooming_line_ids.mapped('price'))

    def _compute_invoice_count(self):
        """Compute the number of invoices linked to the grooming case."""
        for rec in self:
            rec.invoice_count = len(rec.grooming_invoice_id)

    @api.depends('grooming_invoice_id')
    def _compute_payment_ribbon(self):
        """Compute the payment badge based on invoice status."""
        for record in self:
            record.payment_ribbon = record.grooming_invoice_id.payment_state

    @api.onchange('appointment_date')
    def _onchange_appointment_date(self):
        """
            Validate the appointment date to ensure it is not set before the current date.

            This method is triggered when the 'appointment_date' field is changed.
            It raises a ValidationError if the selected appointment date is earlier
            than the current date and time.
            """
        if self.appointment_date < fields.Date.today():
            raise ValidationError(_(
                "Selected appointment date cannot be before today's date."))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to assign grooming appointment number."""
        for vals in vals_list:
            if vals.get('grooming_no', 'New') == 'New':
                vals['grooming_no'] = self.env['ir.sequence'].next_by_code('grooming.sequence') or 'New'
        return super().create(vals_list)

    def action_create_invoice(self):
        """Create an invoice."""
        if not self.grooming_line_ids:
            raise ValidationError(_("Please add at least one grooming service before creating an invoice."))

        for record in self:
            lines = [Command.create({
                'product_id': line.service_id.id,
                'name': line.service_id.name,
                'price_unit': line.price,
            }) for line in record.grooming_line_ids]

            if not lines:
                raise ValidationError(_("Please add at least one service before creating an invoice."))

            invoice = self.env['account.move'].create([{
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.context_today(record),
                'partner_id': record.patient_name_id.owner_name_id.id,
                'currency_id': record.currency_id.id or self.env.company.currency_id.id,
                'grooming_bill_invoice_id': record.id,
                'invoice_line_ids': lines
            }])
            record.grooming_invoice_id = invoice.id
            record.is_invoice = True
            return {
                'name': _('Customer Invoices'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'context': {'default_move_type': 'out_invoice'},
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': invoice.id
            }

    def action_view_invoice(self):
        """Action to view the created invoice."""
        self.ensure_one()
        return {
            'name': _('Customer Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.grooming_invoice_id.id
        }

    def get_top_grooming_products(self):
        """Function to get top 5 grooming products"""
        # Fetch all animal.grooming records
        grooming_data = self.env['animal.grooming'].search([])

        grooming_products = []
        counts = []
        products = []

        # Iterate through each animal.grooming record
        for record in grooming_data:
            # Iterate through each grooming_line_ids in the current animal.grooming record
            for line in record.grooming_line_ids:
                if line.service_id.name:
                    grooming_products.append(line.service_id.name)

        # Count the occurrences of each product
        product_counts = Counter(grooming_products)

        # Get the top 5 products based on their counts
        top_5_products = product_counts.most_common(5)

        # Prepare the result as a list of dictionaries
        for product, count in top_5_products:
            products.append(product)
            counts.append(count)

        result = {'products': products, 'counts': counts}
        return result

