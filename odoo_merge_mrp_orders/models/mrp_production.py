# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Roopchand P M(<https://www.cybrosys.com>)
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
from odoo import models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """
    This class extends the 'mrp.production' model to add a method for merging
    multiple manufacturing orders into a single order.
    """
    _inherit = 'mrp.production'

    def action_merge_order(self):
        """Merge multiple manufacturing orders into a single order.

            Check orders' state, product, BOM, and company consistency.
            return: An action opening the order.mrp.merge wizard.
            Raise UserError for invalid orders.
        """
        product = []
        bom = []
        company = []
        for rec in self:
            if rec.state not in ('draft', 'confirmed', 'progress'):
                raise UserError(
                    _("You can only merge mrp order that "
                      "are in Draft/Confirmed/Progress state"))
            product.append(rec.product_id)
            bom.append(rec.bom_id)
            company.append(rec.company_id.id)
        if len(set(product)) != 1 and len(set(bom)) != 1:
            raise UserError(
                _("You can only merge mrp order that have same product and "
                  "bill of material"))
        if len(set(company)) != 1:
            raise UserError(
                _("You can only merge mrp order in the same company"))
        return {
            'name': "Merge Manufacturing order",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'order.mrp.merge',
            'context': {'records': [rec.id for rec in self],
                        'default_product_id': product[0].id,
                        'default_bom_id': bom[0].id,
                        'default_component_location_id': self[
                            0].location_src_id.id,
                        'default_component_destination_location_id': self[
                            0].location_dest_id.id,
                        'default_manage_qty': self.env[
                            'ir.config_parameter'].sudo().get_param(
                            'odoo_merge_mrp_orders.merge_qty')},
            'target': 'new'
        }
