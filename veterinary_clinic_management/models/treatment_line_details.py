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


class TreatmentLineDetails(models.Model):
    """Class for treatment line details"""
    _name = 'treatment.line.details'
    _description = 'Treatment Line Details'

    description = fields.Char(
        string="Description",
        help="Description of the treatment provided"
    )
    precaution = fields.Char(
        string="Precaution",
        help="Precautions to be taken for the treatment"
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id.id,
        help="Currency in which the charges are calculated"
    )
    charges = fields.Monetary(
        string="Charges",
        currency_field='currency_id',
        help="Cost of the treatment in the specified currency"
    )
    treatment_id = fields.Many2one(
        string="Treatment",
        comodel_name="case.appointments",
        help="Reference to the related case appointment"
    )