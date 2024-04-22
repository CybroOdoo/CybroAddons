# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """Extends the product.template model to generate QR codes for all
    related product variants."""
    _inherit = 'product.template'

    def generate_sequence(self):
        for rec in self.product_variant_ids:
            if not rec.sequence:
                rec.generate_sequence()

    def generate_qr(self):
        """Generate QR codes for all product variants associated with the
        product template."""
        for rec in self.product_variant_ids:
            return rec.generate_qr()