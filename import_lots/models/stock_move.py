# -*- coding: utf-8 -*-
"""Stock Move."""
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class StockMove(models.Model):
    """ Inheriting stock_move to add additional new field and function """
    _inherit = 'stock.move'

    attachment = fields.Binary(string="Upload")

    def action_import_lot(self):
        """ Import and write lots to stock_move_line, using the same checks
        as the Import Lots wizard. """
        self.ensure_one()
        if not self.attachment:
            return None
        return self.env['lot.attachment'].create({
            'move_id': self.id,
            'picking_id': self.picking_id.id,
            'product_id': self.product_id.id,
            'demanded_quantity': self.product_uom_qty,
            'attachment': self.attachment,
        }).action_import_lot()
