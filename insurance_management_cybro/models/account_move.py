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


class AccountMove(models.Model):
    """Inherits 'account.move' to link invoices and bills to insurances
    and claims."""
    _inherit = 'account.move'

    insurance_id = fields.Many2one(
        'insurance.details', index='btree_not_null', ondelete='restrict',
        copy=False, help="Insurance this invoice was generated for")
    claim_id = fields.Many2one(
        'claim.details', string='Insurance Claim', index='btree_not_null',
        ondelete='restrict', copy=False,
        help="Claim this bill was generated for")
