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


class ResUsers(models.Model):
    """Inherit the res_user model to add a field for the WhatsApp Groups
     Enabled or not."""
    _inherit = 'res.users'

    whatsapp_groups_checks = fields.Boolean(
        string='WhatsApp Groups Enabled or not',
        compute="_compute_pos_receipt_invoice_send_whatsapp_group_user",
        help='A field that checks groups is added or not.')

    def _compute_pos_receipt_invoice_send_whatsapp_group_user(self):
        self.whatsapp_groups_checks = self.user_has_groups(
            'pos_receipt_invoice_send_whatsapp.pos_receipt_invoice_send_whatsapp_group_user')
