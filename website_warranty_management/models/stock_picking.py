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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """ Inherit button_validate to create warranty registrations on delivery"""
        res = super(StockPicking, self).button_validate()
        for picking in self:
            if picking.picking_type_code == 'outgoing' and picking.state == 'done':
                sale_order = picking.sale_id
                if sale_order:
                    # Trigger the same logic as action_open_smart_tab but automatically
                    sale_order.action_open_smart_tab()
                    # We can also send emails here if we want or let the registration model handle it
                    registrations = self.env['warranty.registration'].search([
                        ('sale_order_id', '=', sale_order.id)
                    ])
                    for reg in registrations:
                        reg.action_send_confirmation_email()
        return res
