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
from odoo import fields, models


class ResPartner(models.Model):
    """
       Extends the base 'res.partner' model to include additional fields
       and functionality.
    """
    _inherit = 'res.partner'

    return_order_count = fields.Integer(
        compute="_compute_return_order_count", string='Return Orders',
        help="Count of order returned by the customer")

    def _compute_return_order_count(self):
        """Function to calculate the return count per partner."""
        for partner in self:
            partners = partner.sudo().search([('id', 'child_of', partner.id)])
            partner.return_order_count = self.env['sale.return'].sudo().search_count(
                [('partner_id', 'in', partners.ids)]
            )

    def action_open_returns(self):
        """This function returns an action that displays the sale return
        orders from partner."""
        action = self.env['ir.actions.act_window']._for_xml_id(
            'website_multi_product_return_management.sale_return_action')
        domain = []
        if self.is_company:
            domain.append(('partner_id.commercial_partner_id.id', '=', self.id))
        else:
            domain.append(('partner_id.id', '=', self.id))
        action['domain'] = domain
        action['context'] = {'search_default_customer': 1}
        return action
