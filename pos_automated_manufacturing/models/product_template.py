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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    to_create_mrp = fields.Boolean(
        string="To Create MRP Order",
        help="Check this to create an MRP order from POS for this product."
    )
    create_mrp_done = fields.Boolean(
        string="Done MRP Order",
        help="Check this to create the MRP order in 'Done' state from POS."
    )

    @api.constrains('to_create_mrp')
    def _check_bom_existence(self):
        """Ensure BoM exists if to_create_mrp is enabled."""
        for record in self:
            if record.to_create_mrp:
                bom_count = self.env['mrp.bom'].search_count([
                    '|',
                    ('product_tmpl_id', '=', record.id),
                    ('product_id', 'in', record.product_variant_ids.ids)
                ])
                if not bom_count:
                    raise ValidationError(_(
                        "Please create a Bill of Materials (BoM) before enabling "
                        "'To Create MRP Order' for product '%s'."
                    ) % record.name)
