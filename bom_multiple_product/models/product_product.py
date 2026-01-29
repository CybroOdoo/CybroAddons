# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class ProductProduct(models.Model):
    """ Inheriting product form to add a button
    for creating bill of material """
    _inherit = 'product.product'

    def action_create_bom(self):
        """ Open a wizard for creating bill of materials
         based on the selected products."""
        return {
            'name': "Create BOM",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.bom',
            'view_id': self.env.ref(
                'bom_multiple_product.product_bom_view_form').id,
            'target': 'new',
            'context': {
                'default_product_ids': self.env.context.get('active_ids')
            },
        }
