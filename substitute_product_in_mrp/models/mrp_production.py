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
from odoo import models


class MrpProduction(models.Model):
    """Inherited this module to generate MO creation by taking
       substitute products"""
    _inherit = 'mrp.production'

    def action_confirm(self):
        """Creating manufacturing order and if product is out of quantity then
        substituted product is taken"""
        res = super(MrpProduction, self).action_confirm()
        for move in self:
            for bom_line in move.bom_id.bom_line_ids.filtered(
                    lambda x: x.mrp_substitute_product_id):
                for move_raw_id in move.move_raw_ids:
                    if (move_raw_id.product_id.qty_available == 0 and
                            move_raw_id.product_id == bom_line.product_id):
                        if (bom_line.mrp_substitute_product_id.detailed_type ==
                                'product'):
                            if (bom_line.mrp_substitute_product_id.free_qty >=
                                    move_raw_id.product_uom_qty):
                                move_raw_id.product_id = (
                                    bom_line.mrp_substitute_product_id.id)
        return res
