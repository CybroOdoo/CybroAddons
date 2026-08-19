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


class VaccineHistoryDetails(models.Model):
    """
    Model to store the vaccination history of an animal patient.
    This includes details of the vaccines administered and their dates.
    """
    _name = 'vaccine.history.details'
    _description = 'Vaccine History Details'

    vaccine_id = fields.Many2one(
        string="Vaccine",
        comodel_name="animal.vaccine",
        help="Name of the vaccine administered to the animal."
    )
    vaccination_date = fields.Date(
        string="Vaccination Date",
        help="Date when the vaccine was administered to the animal."
    )
    description = fields.Char(
        string="Description",
        help="Additional details or description about the vaccination."
    )
    vaccine_history_id = fields.Many2one(
        string="Vaccine History ID",
        comodel_name="res.patient",
        help="Reference to the patient record for which this vaccination history is recorded."
    )