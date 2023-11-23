# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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
from odoo.tools import float_compare


class ChooseDeliveryPackage(models.TransientModel):
    """This model extends the 'choose.delivery.package' wizard to modify the
    behavior of putting products into packages during the delivery process.
    It customizes the package creation and updates the package type and
    shipping weight for each package based on the chosen delivery package type
     and shipping weight."""
    _inherit = 'choose.delivery.package'

    def action_put_in_pack(self):
        """Override the action_put_in_pack method to modify the behavior of
        putting products into packages during the delivery process.
        This method customizes the package creation and updates the package
        type and shipping weight for each package.
        :return: True if the action is successful"""
        picking_move_lines = self.picking_id.move_line_ids
        if not self.picking_id.picking_type_id.show_reserved and not self.env.context.get(
                'barcode_view'):
            picking_move_lines = self.picking_id.move_line_nosuggest_ids
        move_line_ids = picking_move_lines.filtered(
            lambda ml: float_compare(ml.qty_done, 0.0,
                          precision_rounding=ml.product_uom_id.rounding) > 0
            and not ml.result_package_id)
        if not move_line_ids:
            move_line_ids = picking_move_lines.filtered(
                lambda ml: float_compare(ml.reserved_uom_qty, 0.0,
                                 precision_rounding=ml.product_uom_id.rounding) > 0 and float_compare(ml.qty_done, 0.0,
                                 precision_rounding=ml.product_uom_id.rounding) == 0)
        delivery_packages = self.picking_id._put_in_pack(move_line_ids)
        # Loop through each package and write shipping weight and package type
        # on 'stock_quant_package' if needed
        for package in delivery_packages:
            if self.delivery_package_type_id:
                package.write(
                    {'package_type_id': self.delivery_package_type_id.id})
            if self.shipping_weight:
                package.write({'shipping_weight': self.shipping_weight})
