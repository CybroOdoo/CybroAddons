# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields


class ResUsers(models.Model):
    """Extend res.users model to restrict user access to specific UK regions."""
    _inherit = 'res.users'

    nhs_allowed_welsh_lhb_ids = fields.Many2many(
        'nhs.welsh.lhb',
        'nhs_user_welsh_lhb_rel',
        'user_id',
        'lhb_id',
        string='Allowed Welsh LHBs',
        help="Welsh Local Health Boards this user may see trusts for. Empty = no Welsh access.",
    )
    nhs_allowed_region_ids = fields.Many2many(
        'nhs.region',
        'nhs_user_region_rel',
        'user_id',
        'region_id',
        string='Allowed Regions (Northern Ireland)',
        help="Primarily for Northern Ireland users. Add Northern Ireland here to grant access to all NI HSC Trusts.",
        domain=[('health_system', '=', 'hsc_ni')],
    )

