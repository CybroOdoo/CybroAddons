# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    """In this class we are inheriting the model sale.order and adding
        a new field for signature"""

    _inherit = 'sale.order'

    sale_person_signature = fields.Binary(string='Signature', help="Field for adding the signature of the sales person")
    check_signature = fields.Boolean(compute='_compute_check_signature')

    @api.depends('sale_person_signature')
    def _compute_check_signature(self):
        """In this function computes the value of the boolean field check signature
        which is used to hide/unhide the validate button in the current document"""
        if self.env['ir.config_parameter'].sudo().get_param('sale.sale_document_approve'):
            if self.sale_person_signature:
                self.check_signature = True
            else:
                self.check_signature = False
        else:
            self.check_signature = True
