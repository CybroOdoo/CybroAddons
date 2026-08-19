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
from odoo import api, fields, models


class PrescriptionDetailsLine(models.Model):
    """
        Represents a prescribed medicine line with details like medicine, intake time, quantity, form,
        duration, frequency, and associated prescription.
        """
    _name = "prescription.details.line"
    _description = "Prescription Details Line"

    medicine_id = fields.Many2one(
        string="Medicine",
        comodel_name="product.template",
        domain=[('is_medicine_product', '=', True)],
        context={'default_is_medicine_product': True},
        help="The medicine prescribed, selected from the product list.", required=True)
    intake_time = fields.Selection(
        [('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night')],
        string="Intake Time",
        required=True,
        help="Time of day the medicine should be taken.")
    qty = fields.Integer(
        string="Quantity",
        help="The quantity of medicine prescribed.")
    form = fields.Selection(
        [('liquid', 'Liquid'), ('tablet', 'Tablet'), ('injection', 'Injection')],
        string="Form",
        default='tablet',
        required=True,
        help="The form in which the medicine is prescribed (e.g., tablet, liquid, injection).")
    duration = fields.Integer(
        string="Duration",
        help="Duration for which the medicine should be taken, in days.")
    frequency = fields.Selection(
        [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        string="Frequency",
        default='daily',
        required=True,
        help="How often the medicine should be taken.")
    prescription_id = fields.Many2one(
        string="Prescription ID",
        comodel_name="prescription.orders",
        help="The reference to the prescription order this line belongs to.")

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure any medicine referenced from a prescription line is flagged
        as a medicine product, even if it was quick-created or picked from an
        existing product that wasn't flagged yet."""
        lines = super().create(vals_list)
        for line in lines:
            if line.medicine_id and not line.medicine_id.is_medicine_product:
                line.medicine_id.is_medicine_product = True
        return lines

    def write(self, vals):
        """Keep the medicine flag in sync if the medicine on an existing line is changed."""
        res = super().write(vals)
        if vals.get('medicine_id'):
            for line in self:
                if line.medicine_id and not line.medicine_id.is_medicine_product:
                    line.medicine_id.is_medicine_product = True
        return res