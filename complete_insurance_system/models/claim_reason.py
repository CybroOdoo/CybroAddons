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


class ClaimReason(models.Model):
    """
    Claim Reason Model
    ==================
    This model represents a reason for a claim in the insurance management module.
    Each claim reason has a unique name and an optional color for display purposes.
    """
    _name = 'claim.reason'
    _description = "Claim Reason"

    name = fields.Char(
        string="Name",
        required=True,
        help="The unique name of the claim reason. This field is mandatory."
    )
    color = fields.Integer(
        string='Color',
        help="The color used to represent this claim reason in tags or other visual elements."
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "This Claim reason already exists!"),
    ]
