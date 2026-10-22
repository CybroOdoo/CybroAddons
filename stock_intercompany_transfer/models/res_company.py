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
from odoo import api, fields, models


class ResCompany(models.Model):
    """Inherits 'res.company' and adds fields"""
    _inherit = 'res.company'

    enable_inter_company_transfer = fields.Boolean(
        string='Inter Company Transfer',
        copy=False,
        help="Enable/disable inter company transfer to select delivery/receipts."
    )
    destination_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        help="Select the destination warehouse of the company."
    )
    apply_transfer_type = fields.Selection(
        [
            ('all', 'Delivery and Receipts'),
            ('incoming', 'Receipt'),
            ('outgoing', 'Delivery Order'),
        ],
        string='Apply On',
        default='all',
        help="Select the Picking type to apply the inter company transfer."
    )
    message = fields.Text(
        compute='_compute_message',
        help="Message shown on selecting the type of orders."
    )

    @api.depends('apply_transfer_type', 'destination_warehouse_id')
    def _compute_message(self):
        """Creating the Display message according to the selected type."""
        for rec in self:
            if rec.apply_transfer_type == 'incoming':
                create_type = "Delivery"
                selected_type = "Receipt"
            elif rec.apply_transfer_type == 'outgoing':
                create_type = "Receipt"
                selected_type = "Delivery"
            else:
                create_type = "Delivery Order/Receipt"
                selected_type = "Receipt/Delivery"

            msg = self.env._(
                "Create a %(create_type)s Order when a company validates a "
                "%(selected_type)s Order for %(company)s using %(warehouse)s Warehouse.",
                create_type=create_type,
                selected_type=selected_type,
                company=rec.sudo().name,
                warehouse=rec.sudo().destination_warehouse_id.name,
            )
            rec.message = msg

    @api.onchange('enable_inter_company_transfer')
    def onchange_inter_company_transfer(self):
        """Function to execute on changing the boolean field Inter Company
        transfer to search for the warehouse"""
        company = self._origin
        wh = self.env['stock.warehouse'].sudo().search([
            ('company_id', '=', company.sudo().id)
        ], limit=1, order='id ASC')
        self.destination_warehouse_id = wh
