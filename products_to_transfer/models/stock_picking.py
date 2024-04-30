# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class StockPicking(models.Model):
    """This class extends the base 'stock.picking' model to provide enhanced
       functionality. It introduces a function to open a new window for viewing
       products associated with a picking"""
    _inherit = 'stock.picking'

    def action_view_products(self):
        """Open a new window to view products."""
        return {
            'name': 'View Products',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'domain': [('type', 'in', ['product', 'consu'])],
        }
