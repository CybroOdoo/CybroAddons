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
#############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """ Inherit button_validate to create warranty registrations on delivery"""
        res = super().button_validate()
        for picking in self:
            if picking.picking_type_code == 'outgoing' and picking.state == 'done':
                sale_order = picking.sale_id
                if sale_order:
                    existing_reg_ids = self.env['warranty.registration'].search([
                        ('sale_order_id', '=', sale_order.id)
                    ]).ids
                    sale_order.action_open_smart_tab()
                    new_registrations = self.env['warranty.registration'].search([
                        ('sale_order_id', '=', sale_order.id),
                        ('id', 'not in', existing_reg_ids),
                    ])
                    for reg in new_registrations:
                        reg.action_send_confirmation_email()
        return res
