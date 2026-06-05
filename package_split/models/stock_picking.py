# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models
from collections import defaultdict


class Picking(models.Model):
    """Inheriting the stock picking model to change the package creation method
    based on package category provided inside the product form."""
    _inherit = 'stock.picking'

    def _put_in_pack(self, move_line_ids):
        """For each product in the orderline with the same package category,
            it creates packages and adds the corresponding products into the
            package when validating the delivery"""

        move_lines_by_category = defaultdict(list)
        for move_line in move_line_ids:
            category = move_line.product_id.package_category_id
            move_lines_by_category[category].append(move_line)
        packages = []
        for category, move_lines in move_lines_by_category.items():
            package = self.env['stock.quant.package'].create({})
            if category:
                package_name = f"{package.name}-{category.name}"
                package.write({'name': package_name})
            package_type = move_lines[0].move_id.product_packaging_id.package_type_id
            if len(package_type) == 1:
                package.package_type_id = package_type
            for move_line in move_lines:
                default_dest_location = move_line._get_default_dest_location()
                move_line.location_dest_id = default_dest_location._get_putaway_strategy(
                    product=move_line.product_id,
                    quantity=move_line.quantity,
                    package=package
                )
                move_line.write({
                    'result_package_id': package.id,
                })
            if len(self) == 1:
                self.env['stock.package_level'].create({
                    'package_id': package.id,
                    'picking_id': self.id,
                    'location_id': False,
                    'location_dest_id': move_lines[0].location_dest_id.id,
                    'move_line_ids': [(6, 0, [ml.id for ml in move_lines])],
                    'company_id': self.company_id.id,
                })

            packages.append(package)
        return packages
