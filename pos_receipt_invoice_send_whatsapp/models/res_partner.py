###############################################################################
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
###############################################################################
# pylint: disable=missing-module-docstring,unknown-option-value,too-few-public-methods
from odoo import api, fields, models


class ResPartner(models.Model):
    """Inherit the res_partner model to add a field for the WhatsApp number."""

    _inherit = "res.partner"

    whatsapp_number = fields.Char(
        string="WhatsApp Number",
        help="A field is needed to add the WhatsApp number of the partner.",
    )

    @api.model
    def _load_pos_data_fields(self, config):
        """Add whatsapp_number to the partner fields loaded in POS data."""
        pos_fields = super()._load_pos_data_fields(config)
        pos_fields.append("whatsapp_number")
        return pos_fields
