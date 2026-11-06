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


class PosConfig(models.Model):
    """Inherit the pos_config model to add additional fields
    to the configuration settings."""

    _inherit = "pos.config"

    pos_whatsapp_enabled = fields.Boolean(
        string="WhatsApp Enabled",
        help="Checks WhatsApp Enabled button active or not",
    )
    apply_send_receipt_or_invoice = fields.Selection(
        [
            ("send_receipt", "Send Receipt"),
            ("send_invoice", "Send Invoice"),
            ("both", "Both Receipt and Invoice"),
        ],
        string="Apply Send Receipt or Invoice",
        default="both",
        help="Select Receipt, Invoice, or Both for sending to WhatsApp.",
    )
