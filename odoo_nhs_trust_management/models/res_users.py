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
    _inherit = 'res.users'

    nhs_allowed_icb_ids = fields.Many2many(
        'nhs.icb',
        'nhs_user_icb_rel',
        'user_id',
        'icb_id',
        string='Allowed ICBs (England)',
        help='Users will only be able to see NHS Trusts associated with these Integrated Care Boards (ICBs).'
    )
    nhs_allowed_health_board_ids = fields.Many2many(
        'nhs.health.board',
        'nhs_user_health_board_rel',
        'user_id',
        'health_board_id',
        string='Allowed Health Boards (Scotland)',
        help='Users will only be able to see NHS Trusts associated with these Scottish Health Boards.'
    )
