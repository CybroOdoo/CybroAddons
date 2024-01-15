# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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


class ResConfigSettings(models.TransientModel):
    """Declaring a class for ResConfigSettings and Adding fields"""
    _inherit = 'res.config.settings'

    is_takeaway = fields.Boolean(
        string='Pos TakeAway',
        related="pos_config_id.is_pos_takeaway",
        help="TakeAway, Dine-in on Restaurant",
        readonly=False,
    )
    is_generate_token = fields.Boolean(
        string='Generate Token',
        related="pos_config_id.is_generate_token",
        help="This Token number starts from 1",
        readonly=False,
    )
    pos_token = fields.Integer(
        string="Token",
        help="The token will start from 1.",
        related="pos_config_id.pos_token"
    )
