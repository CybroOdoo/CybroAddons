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
from collections import defaultdict
from odoo import api, fields, models, _


class PrescriptionOrders(models.Model):
    """Fields to store prescription orders in veterinary clinic Management"""
    _name = 'prescription.orders'
    _inherit = 'mail.thread'
    _rec_name = 'prescription_no'
    _description = 'Prescription Orders'

    prescription_no = fields.Char(
        string="Prescription No",
        default=lambda self: _('New'),
        copy=False,
        readonly=True,
        tracking=True,
        help="Unique number for the prescription, automatically generated.")
    patient_id = fields.Many2one(
        string="Animal",
        comodel_name="case.appointments",
        help="The animal patient for whom the prescription is issued.",
        required=True)
    customer_id = fields.Many2one(
        string="Customer",
        related="patient_id.owner_id",
        help="The owner of the animal patient.")
    doctor_id = fields.Many2one(
        string="Doctor",
        comodel_name="veterinary.employees",
        domain=[('staff', '=', 'doctor')],
        help="The doctor who prescribed the medication.",
        required=True)
    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
        copy="False",
        help="The date the prescription was issued.")
    pharmacist_id = fields.Many2one(
        string="Pharmacist",
        comodel_name="res.partner",
        ondelete='cascade',
        copy="False",
        help="The pharmacist responsible for dispensing the medication.",
        required=True)
    prescription_line_ids = fields.One2many(
        'prescription.details.line',
        'prescription_id',
        string="Prescription Details",
        copy="False",
        help="Details of the medications prescribed.")

    @api.model_create_multi
    def create(self, vals_list):
        """Function to assign prescription appointment No"""
        for vals in vals_list:
            if vals.get('prescription_no', 'New') == 'New':
                vals['prescription_no'] = self.env['ir.sequence'].next_by_code('prescription.sequence') or 'New'
        return super().create(vals_list)

    def get_top_medicines(self):
        """Function to get top 5 products"""
        # Fetch all prescription.orders records
        prescription_data = self.env['prescription.orders'].search([])

        medicine_products = defaultdict(int)
        products = []
        counts = []

        # Iterate through each prescription.orders record
        for record in prescription_data:
            # Iterate through each prescription_line_ids in the current prescription.orders record
            for line in record.prescription_line_ids:
                if line.medicine_id.name and line.qty:
                    # Sum the quantity of each medicine
                    medicine_products[line.medicine_id.name] += line.qty

        # Get the top 5 medicines based on their quantity
        top_5_medicines = sorted(medicine_products.items(), key=lambda x: x[1], reverse=True)[:5]

        # Prepare the result as a list of dictionaries
        for medicine, count in top_5_medicines:
            products.append(medicine)
            counts.append(count)

        result = {'products': products, 'counts': counts}
        return result
