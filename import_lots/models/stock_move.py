# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models, _


class StockMove(models.Model):
    """Inheriting stock_move to add additional new field and function"""
    _inherit = 'stock.move'

    attachment = fields.Binary(string="Upload")

    def action_return_lot_wizard(self):
        """Return lot_attachment Wizard"""
        return {
            'name': _('Import Lots'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'lot.attachment',
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
                'default_demanded_quantity': self.product_uom_qty,
                'default_picking_id': self.picking_id.id,
                'default_move_id': self.id
            },
        }
