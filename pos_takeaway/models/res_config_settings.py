#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

    pos_is_pos_takeaway = fields.Boolean(
        string='POS Take Away',
        related="pos_config_id.is_pos_takeaway",
        help="Enable Take Away and Dine-In orders in the restaurant POS",
        readonly=False,
    )
    pos_is_generate_token = fields.Boolean(
        string='Generate Token',
        related="pos_config_id.is_generate_token",
        help="Generate a token number for Take Away orders",
        readonly=False,
    )
    pos_pos_token = fields.Integer(
        string="Token",
        help="Last token number issued by this POS.",
        related="pos_config_id.pos_token",
        readonly=True,
    )
