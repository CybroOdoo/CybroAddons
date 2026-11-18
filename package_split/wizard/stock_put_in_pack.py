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
from odoo import models


class StockPutInPack(models.TransientModel):
    """Extend the Put in Pack wizard to support category-split packages."""

    _inherit = 'stock.put.in.pack'

    def action_put_in_pack(self):
        """Execute Put in Pack and preserve wizard settings across split packages."""
        result = super().action_put_in_pack()
        if (
            self.move_line_ids
            and self.env['ir.config_parameter'].sudo().get_bool(
                'package_split.enable_package_split',
            )
        ):
            packages = self.move_line_ids.result_package_id
            if packages:
                vals = {}
                if self.package_type_id:
                    vals['package_type_id'] = self.package_type_id.id
                if self.shipping_weight and len(packages) == 1:
                    vals['shipping_weight'] = self.shipping_weight
                if vals:
                    packages.write(vals)
        return result
