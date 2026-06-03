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


class InsurancePolicy(models.Model):
    """
    Represents an insurance policy that includes information about the policy type,
    coverage amount, related documents, and other details associated with the insurance policy.
    """
    _name = 'insurance.policy'
    _rec_name = 'insurance_policy_id'
    _description = 'Insurance Policy'

    insurance_policy_id = fields.Many2one(
        string='Insurance Policy',
        comodel_name="insurance.policy.sub.category",
        required=True,
        help='The name of the insurance policy.'
    )
    policy_number = fields.Char(
        string='Policy Number',
        required=True,
        help='The unique identifier for the insurance policy.'
    )
    policy_category_id = fields.Many2one(
        related='insurance_policy_id.category_id',
        string='Policy Category',
        help='Category to which the insurance policy belongs, such as health, auto, etc.'
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id.id,
        help='Currency used in the insurance policy.'
    )
    insurance_amount = fields.Monetary(
        string='Insurance Amount',
        required=True,
        help='The amount covered by the insurance policy.'
    )
    claim_amount = fields.Monetary(
        string='Claim Amount',
        required=True,
        help='The amount that can be claimed under the insurance policy.'
    )
    policy_document_ids = fields.Many2many(
        string='Policy Document',
        comodel_name="insured.document",
        required=True,
        help='Documents related to the insurance policy.'
    )
    claim_document_ids = fields.Many2many(
        string='Claim Document',
        comodel_name="claim.document",
        required=True,
        help='Documents related to claims made under the insurance policy.'
    )
    policy_description = fields.Html(
        string='Policy Description',
        help='Detailed description of the insurance policy.'
    )
    terms_condition = fields.Html(
        string='Terms and Conditions',
        help='Terms and conditions associated with the insurance policy.'
    )
