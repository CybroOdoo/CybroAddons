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
from odoo import fields, models


class MedicalHistoryDetails(models.Model):
    """
    Model to store the medical history of an animal patient in a veterinary clinic management system.
    This includes details of diseases, treatments, and allergies.
    """
    _name = 'medical.history.details'
    _description = 'Medical History Details'

    disease_name_id = fields.Many2one(
        string="Disease Name",
        comodel_name="disease.types",
        help="Name of the disease diagnosed in the animal."
    )
    description = fields.Char(
        string="Description",
        related="disease_name_id.name",
        help="Description of the disease."
    )
    start_date = fields.Date(
        string="Start Date",
        help="The date when the disease symptoms started or were diagnosed."
    )
    end_date = fields.Date(
        string="End Date",
        help="The date when the disease symptoms ended or the treatment concluded."
    )
    medicine_id = fields.Many2one(
        string="Medicine Name",
        comodel_name="product.template",
        domain=[('is_medicine_product', '=', True)],
        help="Name of the medicine prescribed for the disease."
    )
    allergy = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string="Allergy",
        default='no',
        required=True,
        help="Indicates whether the animal has any allergies related to the disease or medicine."
    )
    allergy_description = fields.Char(
        string="Allergy Description",
        help="Description of the allergy, if any."
    )
    medical_history_id = fields.Many2one(
        string="Medical History ID",
        comodel_name="res.patient",
        help="Reference to the patient record for which this medical history is recorded."
    )