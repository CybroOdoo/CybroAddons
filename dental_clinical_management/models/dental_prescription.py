# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import api, fields, models, _


class DentalPrescription(models.Model):
    """Prescription of patient from the dental clinic"""
    _name = 'dental.prescription'
    _description = "Dental Prescription"
    _inherit = ['mail.thread']
    _rec_name = "sequence_no"

    sequence_no = fields.Char(string='Sequence No', required=True,
                              readonly=True, default=lambda self: self.env._('New'),
                              help="Sequence number of the dental prescription")
    appointment_ids = fields.Many2many('dental.appointment',
                                       string="Appointment",
                                       compute="_compute_appointment_ids",
                                       help="All appointments created")
    appointment_id = fields.Many2one('dental.appointment',
                                     string="Appointment",
                                     domain="[('id','in',appointment_ids)]",
                                     required=True,
                                     help="All appointments created")
    patient_id = fields.Many2one(related="appointment_id.patient_id",
                                 string="Patient",
                                 required=True,
                                 help="name of the patient")
    token_no = fields.Integer(related="appointment_id.token_no",
                              string="Token Number",
                              help="Token number of the patient")
    treatment_id = fields.Many2one('dental.treatment',
                                   string="Treatment",
                                   help="Name of the treatment done for patient")
    cost = fields.Float(related="treatment_id.cost",
                        string="Treatment Cost",
                        help="Cost of treatment")
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  required=True,
                                  help="To add the currency type in cost")
    prescribed_doctor_id = fields.Many2one(related="appointment_id.doctor_id",
                                           string='Prescribed Doctor',
                                           required=True,
                                           help="Doctor who is prescribed")
    prescription_date = fields.Date(related="appointment_id.date",
                                    string='Prescription Date',
                                    required=True,
                                    help="Date of the prescription")
    state = fields.Selection([('new', 'New'),
                              ('done', 'Prescribed'),
                              ('invoiced', 'Invoiced')],
                             default="new",
                             string="state",
                             help="state of the appointment")
    medicine_ids = fields.One2many('dental.prescription_lines',
                                   'prescription_id',
                                   string="Medicine",
                                   help="medicines")
    invoice_data_id = fields.Many2one(comodel_name="account.move", string="Invoice Data",
                                      help="Invoice Data")
    grand_total = fields.Float(compute="_compute_grand_total",
                               string="Grand Total",
                               help="Get the grand total amount")

    @api.model
    def create(self, vals):
        """Function declared for creating sequence Number for patients"""
        if vals.get('sequence_no', self.env._('New')) == self.env._('New'):
            vals['sequence_no'] = self.env['ir.sequence'].next_by_code(
                'dental.prescriptions') or self.env._('New')
        res = super(DentalPrescription, self).create(vals)
        return res

    @api.depends('appointment_id')
    def _compute_appointment_ids(self):
        """Computes and assigns the `appointment_ids` field for each record.
        This method searches for all `dental.appointment` records that have
        a state of `new` and a date equal to today's date. It then updates
        the `appointment_ids` field of each `DentalPrescription` record
        with the IDs of these found appointments."""
        for rec in self:
            rec.appointment_ids = self.env['dental.appointment'].search(
                [('state', '=', 'new'), ('date', '=', fields.Date.today())]).ids

    def action_prescribed(self):
        """Marks the prescription and its associated appointment as `done`.
        This method updates the state of both the DentalPrescription instance
        and its linked dental.appointment instance to `done`, indicating that
        the prescription has been finalized and the appointment has been completed.
        """
        self.state = 'done'
        self.appointment_id.state = 'done'

    def create_invoice(self):
        """Create an invoice based on the patient invoice."""
        self.ensure_one()
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.id,
            'invoice_line_ids': [
                fields.Command.create({
                    'name': self.treatment_id.name,
                    'quantity': 1,
                    'price_unit': self.cost,
                })
            ]
        }
        invoice = self.env['account.move'].create(invoice_vals)
        for rec in self.medicine_ids:
            product_id = self.env['product.product'].search([
                ('product_tmpl_id', '=', rec.medicament_id.id)])
            invoice['invoice_line_ids'] = [(0, 0, {
                'product_id': product_id.id,
                'name': rec.display_name,
                'quantity': rec.quantity,
                'price_unit': rec.price,
            })]
        self.invoice_data_id = invoice.id
        invoice.action_post()
        self.state = 'invoiced'
        return {
            'name': self.env._('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_data_id.id,
        }

    def action_view_invoice(self):
        """Invoice view"""
        return {
            'name': self.env._('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_data_id.id,
        }

    def _compute_grand_total(self):
        """Computes the grand total cost of the dental prescription.

        This method initializes the grand total with the cost of the treatment
        and then iterates over all the prescribed medicines, adding their total
        cost to the grand total. The grand total is stored in the `grand_total`
        field of the `DentalPrescription` model."""
        self.grand_total = self.cost
        for rec in self.medicine_ids:
            self.grand_total += rec.total


class DentalPrescriptionLines(models.Model):
    """Prescription lines of the dental clinic prescription"""
    _name = 'dental.prescription_lines'
    _description = "Dental Prescriptions Lines"
    _rec_name = "medicament_id"

    medicament_id = fields.Many2one('product.template',
                                    domain="[('is_medicine', '=', True)]",
                                    string="Medicament",
                                    help="Name of the medicine")
    generic_name = fields.Char(string="Generic Name",
                               related="medicament_id.generic_name",
                               help="Generic name of the medicament")
    dosage_strength = fields.Integer(string="Dosage Strength",
                                     related="medicament_id.dosage_strength",
                                     help="Dosage strength of medicament")
    medicament_form = fields.Selection([('tablet', 'Tablets'),
                             ('capsule', 'Capsules'),
                             ('liquid', 'Liquid'),
                             ('injection', 'Injections')],
                            string="Medicament Form",
                            required=True,
                            help="Add the form of the medicine")
    quantity = fields.Integer(string="Quantity",
                              required=True,
                              help="Quantity of medicine")
    frequency_id = fields.Many2one('medicine.frequency',
                                   string="Frequency",
                                   required=True,
                                   help="Frequency of medicine")
    price = fields.Float(related='medicament_id.list_price',
                         string="Price",
                         help="Cost of medicine")
    total = fields.Float(string="Total Price",
                         help="Total price of medicine")
    prescription_id = fields.Many2one('dental.prescription',
                                      help="Relate the model with dental_prescription")

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """Updates the total price of the medicament based on the quantity.
        This method is triggered by an onchange event of the `quantity` field.
        It calculates the total price by multiplying the `quantity` of the
        medicament by its `price` and updates the `total` field with the new value.
        """
        for rec in self:
            rec.total = rec.price * rec.quantity
