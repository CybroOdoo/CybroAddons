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


class ResUsers(models.Model):
    """Inherit the res_user model to add a field for the WhatsApp Groups
    Enabled or not."""

    _inherit = "res.users"

    whatsapp_groups_checks = fields.Boolean(
        string="WhatsApp Groups Enabled or not",
        compute="_compute_pos_receipt_invoice_send_whatsapp_group_user",
        help="A field that checks groups is added or not.",
    )

    def _compute_pos_receipt_invoice_send_whatsapp_group_user(self):
        """Compute whether the user belongs to the WhatsApp user group."""
        group = (
            "pos_receipt_invoice_send_whatsapp."
            "pos_receipt_invoice_send_whatsapp_group_user"
        )
        for user in self:
            user.whatsapp_groups_checks = user.has_group(group)

    @api.model
    def _load_pos_data_fields(self, config):
        """Add whatsapp_groups_checks to the user fields loaded in POS data."""
        pos_fields = super()._load_pos_data_fields(config)
        pos_fields.append("whatsapp_groups_checks")
        return pos_fields
