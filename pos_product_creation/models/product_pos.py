# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: LINTO C T(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, api


class ProductFromPos(models.Model):
    _inherit = 'product.product'

    @api.model
    def create_product_pos(self, vals):
        type = None        
        if vals.get('type') == 'Stockable':
            type = 'product'
        elif vals.get('type') == 'Consumable':
            type = 'consu'
        elif vals.get('type') == 'Service':
            type = 'service'
        category = self.env['product.category'].search([('name', '=', vals.get('category'))], limit=1)
        uom_id = self.env['uom.uom'].search([('name', '=', vals.get('unit'))], limit=1)
        new_vals = {
            'name': vals.get('name'),
            'display_name': vals.get('name'),
            'type': type,
            'categ_id': category.id if category else None,
            'list_price': vals.get('price') if vals.get('price') else 1,
            'available_in_pos': True,
            'sale_ok': True,
            'uom_id': uom_id.id,
            'uom_po_id': uom_id.id
            }
        rec = self.env['product.product'].create(new_vals)
        new_vals['id'] = rec.id
        new_vals['lst_price'] = vals.get('price') if vals.get('price') else 1
        new_vals['standard_price'] = vals.get('price') if vals.get('price') else 1
        new_vals['pos_categ_id'] = [rec.pos_categ_id.id] if rec.pos_categ_id else None
        new_vals['taxes_id'] = [rec.taxes_id.id] if rec.taxes_id else []
        new_vals['barcode'] = rec.barcode
        new_vals['default_code'] = rec.default_code
        new_vals['to_weight'] = rec.to_weight
        new_vals['uom_id'] = [rec.uom_id.id, rec.uom_id.name]
        new_vals['description_sale'] = rec.description_sale
        new_vals['description'] = rec.description
        new_vals['product_tmpl_id'] = [rec.product_tmpl_id.id]
        new_vals['tracking'] = rec.tracking
        
        return new_vals