#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class PolicyDetails(models.Model):
    """Defines the policies that can be issued to customers."""
    _name = 'policy.details'
    _description = "Policy Details"
    _check_company_auto = True

    name = fields.Char(required=True, help="Name of the policy")
    company_id = fields.Many2one(
        'res.company', required=True, index=True,
        default=lambda self: self.env.company,
        help="Company this policy belongs to")
    policy_type_id = fields.Many2one(
        'policy.type', required=True,
        help="Select the policy type")
    payment_type_ids = fields.Many2many(
        'payment.type',
        help="Select the payment types allowed for the policy")
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.company.currency_id,
        help="Select the currency")
    amount = fields.Monetary(required=True,
                             help="Amount of the policy")
    note_field = fields.Html(string='Comment', help="Specify the comments")
