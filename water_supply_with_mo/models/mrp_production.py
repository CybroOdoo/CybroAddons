# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models


class MrpProduction(models.Model):
    """ This class adds additional fields and overrides the 'create' method
     for specific functionality."""
    _inherit = 'mrp.production'

    manufacturing_order_id = fields.Many2one('manufacturing.order.creation',
                                             string='MO Order',
                                             help='Manufacturing order.')
    supply_id = fields.Many2one('water.supply.request',
                                string='Water Supply Request',
                                help='Displaying water supply request')

    @api.model_create_multi
    def create(self, vals):
        """Create a new Manufacturing Production."""
        records = super(MrpProduction, self).create(vals)
        for res in records:
            default_mo_context_id = res._context.get(
                'default_manufacturing_order_id')
            default_manufacturing_order_id = self.env[
                'manufacturing.order.creation'].browse(default_mo_context_id)
            default_manufacturing_order_id.mrp_id = res
            default_manufacturing_order_id.bom_id = res.bom_id.id
            if default_manufacturing_order_id.mrp_id:
                default_manufacturing_order_id.write({'is_mo': False})
        return records
