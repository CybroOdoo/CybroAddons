# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import _, models


class StockPicking(models.Model):
    """This class extends the base 'stock.picking' model to provide enhanced
       functionality. It introduces a function to open a new window for viewing
       products associated with a picking"""
    _inherit = 'stock.picking'

    def action_view_products(self):
        """Open a new window to view products."""
        self.ensure_one()
        return {
            'name': _('View Products'),
            'view_mode': 'kanban,list,form',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'domain': [('type', 'in', ['consu', 'combo'])],
            'context': {
                'picking_id': self.id,
                'default_picking_id': self.id,
            },
        }
