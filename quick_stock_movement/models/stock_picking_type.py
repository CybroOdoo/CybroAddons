# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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


class StockPickingType(models.Model):
    """Inherits the model stock.picking.type and adds extra functionality to
    open the wizard to create the stock picking"""
    _inherit = 'stock.picking.type'

    def action_transfer_stock(self):
        """Open a pop-up to make the stock transfer"""
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': "Stock Transfer",
            'view_mode': 'form',
            'res_model': 'stock.transfer'
        }
