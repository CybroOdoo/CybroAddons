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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit the res_config_settings model to add a selection field
    and a boolean field for enabling WhatsApp functionality."""

    _inherit = "res.config.settings"

    pos_whatsapp_enabled = fields.Boolean(
        related="pos_config_id.pos_whatsapp_enabled",
        readonly=False,
        help="Checks WhatsApp Enabled button active or not",
    )
    apply_send_receipt_or_invoice = fields.Selection(
        related="pos_config_id.apply_send_receipt_or_invoice",
        readonly=False,
        help="Select Receipt, Invoice, or Both for sending to WhatsApp.",
    )
