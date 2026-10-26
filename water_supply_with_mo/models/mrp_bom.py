# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import api, models


class MrpBom(models.Model):
    """ This class extends the standard MRP Bill of Materials (BOM) model
     to incorporate changes related to variants."""
    _inherit = 'mrp.bom'

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        """Update the product ID based on the selected product template ID."""
        if self.product_tmpl_id:
            self.product_id = self.env['product.product'].search(
                [('product_tmpl_id', '=', self.product_tmpl_id.id)], limit=1
            )
        else:
            self.product_id = False
