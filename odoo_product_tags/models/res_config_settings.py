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
from ast import literal_eval
from odoo import Command, api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited the class res.config.settings to add the fields."""
    _inherit = 'res.config.settings'

    product_tag_ids = fields.Many2many(
        'product.tag', string='Default Product Tags',
        help='To add the default product tags while creating new products',
    )

    def set_values(self):
        """Save values in the settings product tag fields."""
        res = super().set_values()
        self.env['ir.config_parameter'].set_str(
            'odoo_product_tags.product_tag_ids',
            str(self.product_tag_ids.ids)
        )
        return res

    @api.model
    def get_values(self):
        """Get values for product tag fields in the settings
        and assign the value to that fields."""
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        pro_tag_ids = params.get_str(
            'odoo_product_tags.product_tag_ids')
        if pro_tag_ids:
            try:
                tag_ids = literal_eval(pro_tag_ids)
            except (ValueError, SyntaxError):
                tag_ids = []
            if tag_ids:
                res.update(
                    product_tag_ids=[Command.set(tag_ids)]
                )
        return res


