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


class SaleOrderLine(models.Model):
    """ Inherits model 'sale.order.line' and adds field 'recipient' """
    _inherit = 'sale.order.line'

    recipient_id = fields.Many2one('res.partner', string='Recipient',
                                   help='Choose a recipient for splitting '
                                        'the delivery',
                                   domain="['|', ('company_id', '=', False), "
                                          "('company_id', '=', company_id)]",
                                   check_company=True)

    @api.onchange("product_template_id")
    def _onchange_product_template_id(self):
        """Update recipients in order lines with the customer of sale order as
        default recipient"""
        res = super()._onchange_product_template_id()
        if self.order_id.is_delivery_split:
            for line in self:
                if not line.recipient_id:
                    line.recipient_id = line.order_id.partner_id.id
        return res

    def _prepare_procurement_values(self, **kwargs):
        """ Add partner_id to procurement values if delivery_split is enabled """
        self.ensure_one()
        values = super()._prepare_procurement_values(**kwargs)

        if self.order_id.is_delivery_split:
            recipient = self.recipient_id or self.order_id.partner_id
            if recipient:
                values.update({"partner_id": recipient.id})

        return values
