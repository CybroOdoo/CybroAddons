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


class AccountMove(models.Model):
    """
    Inherit account.move to include additional fields for managing insurance
    and commission details in invoices.
    """
    _inherit = 'account.move'

    commission_id = fields.Many2one(
        'res.insurance',
        string='Commission',
        help="Provide the commission details associated with this invoice."
    )

    insurance_id = fields.Many2one(
        'res.insurance',
        string='Insurance Policy',
        readonly=True,
        help="Select the insurance policy related to this invoice. This field is read-only."
    )

    claim_id = fields.Many2one(
        'insurance.claim',
        string='Insurance Claim',
        help="Provide the claim details associated with this invoice."
    )
