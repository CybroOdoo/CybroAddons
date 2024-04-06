# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class PurchaseOrder(models.Model):
    """To add purchase notes"""
    _inherit = "purchase.order"

    def _default_purchase_notes(self):
        """To set purchase notes from purchase configuration."""
        note = self.env['ir.config_parameter'].sudo().get_param(
            'purchase_notes')
        return note

    purchase_notes = fields.Html(string='Notes', translate=True,
                                 help="Notes displayed in Purchase reports.",
                                 default=_default_purchase_notes, copy=False)
