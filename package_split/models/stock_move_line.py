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
from collections import defaultdict

from odoo import models


class StockMoveLine(models.Model):
    """Extend stock move lines to split packages by product package category."""

    _inherit = 'stock.move.line'

    def action_put_in_pack(
        self,
        *,
        package_id=False,
        package_type_id=False,
        package_name=False,
        package_capacity=None,
    ):
        """Group move lines by package category and create separate packages."""
        if not self.env['ir.config_parameter'].sudo().get_bool(
            'package_split.enable_package_split',
        ):
            return super().action_put_in_pack(
                package_id=package_id,
                package_type_id=package_type_id,
                package_name=package_name,
                package_capacity=package_capacity,
            )

        move_lines = self
        if package_capacity and len(self) == 1 and package_capacity != self.quantity:
            return move_lines._split_in_chunk(
                package_capacity,
                package_type_id,
                package_id=package_id,
            )

        if self.env.context.get('all_move_line_ids'):
            move_lines = self.env['stock.move.line'].browse(
                self.env.context['all_move_line_ids'],
            )

        force_move_lines = bool(self.env.context.get('force_move_lines'))
        move_lines_to_pack, packages_to_pack = (
            move_lines._get_lines_and_packages_to_pack(
                picked_first=not force_move_lines,
            )
        )

        if not move_lines_to_pack:
            if packages_to_pack:
                return packages_to_pack.action_put_in_pack(
                    package_id=package_id,
                    package_type_id=package_type_id,
                    package_name=package_name,
                )
            return False

        action = move_lines_to_pack._pre_put_in_pack_hook(
            move_lines,
            package_id,
            package_type_id,
            package_name,
            self.env.context.get('from_package_wizard'),
        )
        if action:
            return action

        move_lines_by_category = defaultdict(lambda: self.env['stock.move.line'])
        for move_line in move_lines_to_pack:
            category = move_line.product_id.package_category_id
            move_lines_by_category[category] |= move_line

        packages = self.env['stock.package']
        hook_action = False
        use_single_target = len(move_lines_by_category) == 1 and bool(package_id)

        for category, lines in move_lines_by_category.items():
            pkg_type_id = package_type_id
            if not pkg_type_id:
                uom_package_type = lines.move_id.packaging_uom_id.package_type_id
                if len(uom_package_type) == 1:
                    pkg_type_id = uom_package_type.id

            target_package_id = package_id if use_single_target else False
            package = lines._put_in_pack(
                package_id=target_package_id,
                package_type_id=pkg_type_id,
                package_name=package_name,
            )
            if package:
                if category and package.name and not package.name.endswith(
                    f"-{category.name}",
                ):
                    package.write({'name': f"{package.name}-{category.name}"})
                packages |= package
                post_result = lines._post_put_in_pack_hook(package)
                if isinstance(post_result, dict):
                    hook_action = post_result

        if hook_action and not force_move_lines:
            return hook_action

        if packages_to_pack:
            if packages:
                packages_to_pack -= packages
                package_id = packages[0].id
            if packages_to_pack:
                additional_packages = packages_to_pack.action_put_in_pack(
                    package_id=package_id,
                    package_type_id=package_type_id,
                    package_name=package_name,
                )
                if isinstance(additional_packages, dict):
                    return additional_packages
                if additional_packages:
                    packages |= additional_packages

        return packages[0] if packages else False
