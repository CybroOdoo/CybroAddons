# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class PosConfig(models.Model):
    """Inherit the pos_config model to add additional fields
    to the configuration settings."""
    _inherit = 'pos.config'

    pos_whatsapp_enabled = fields.Boolean(string='WhatsApp Enabled',
                                          help='Checks WhatsApp Enabled button '
                                               'active or not')
    apply_send_receipt_or_invoice = fields.Selection([
        ('send_receipt', 'Send Receipt'),
        ('send_invoice', 'Send Invoice')
    ], string="Apply Send Receipt or Invoice",
        help='Select either Receipt or Invoice for sending to WhatsApp.')
