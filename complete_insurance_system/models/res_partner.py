# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class ResPartner(models.Model):
    """
        Inherit the res.partner model to include agent-related fields
        and a one-to-many relationship with insurance details.

        This class extends the partner model to indicate whether a partner
        is an agent and to maintain a list of insurance details associated
        with the partner.
        """
    _inherit = "res.partner"

    agent = fields.Boolean(
        string="Agent",
        default=False,
        help="Indicate if the partner is an agent."
    )
    insurance_line_ids = fields.One2many(
        string="Insurance Details",
        comodel_name="insurance.details",
        inverse_name="insurance_detail_id",
        copy=False,
        help="List of insurance details associated with this partner."
    )


class InsuranceDetails(models.Model):
    """
        Model to store detailed information about insurance policies.

        This model includes the unique identifier for the insurance,
        references to the policy holder and policy category, as well
        as important dates and associated commission bills.
        """
    _name = 'insurance.details'
    _description = 'Insurance Details'

    insurance_id = fields.Char(
        string="Insurance",
        help="Unique identifier for the insurance policy."
    )
    policy_holder_id = fields.Many2one(
        string="Policy Holder",
        comodel_name="res.partner",
        help="Reference to the policy holder of the insurance."
    )
    policy_category_id = fields.Many2one(
        string="Policy Category",
        comodel_name="insurance.policy.category",
        help="Category of the insurance policy."
    )
    issue_date = fields.Date(
        string="Issue Date",
        help="Date when the insurance policy was issued."
    )
    expiry_date = fields.Date(
        string="Expiry Date",
        help="Date when the insurance policy expires."
    )
    commission_bill_id = fields.Char(
        string="Invoice",
        help="Identifier for the commission bill related to the insurance."
    )
    insurance_detail_id = fields.Many2one(
        string="Insurance Detail Id",
        comodel_name="res.partner",
        help="Reference to the partner associated with this insurance detail."
    )
