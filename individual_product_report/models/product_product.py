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
from odoo.exceptions import AccessError


class ProductProduct(models.Model):
    """ Inheriting product.product to add Sale Report Smart button"""
    _inherit = 'product.product'

    def action_view_sales_report(self):
        """ To view the graph view on click of Sales Report Button in
        product.product model"""
        self.check_access('read')
        if not self.env.user.has_group('sales_team.group_sale_salesman'):
            raise AccessError(
                _("You do not have the access rights to view sales reports.")
            )
        self.env['sale.report'].check_access('read')
        action = self.env['ir.actions.act_window']._for_xml_id(
            'individual_product_report.report_sales_product_graph'
        )
        action['domain'] = [('product_id', 'in', self.ids)]
        action['context'] = {
            'graph_measure': ['product_uom_qty'],
            'active_id': self.env.context.get('active_id'),
            'active_model': 'sale.report',
            'search_default_Sales': 1,
            'time_ranges': {'field': 'date', 'range': 'last_365_days'},
            'groupby': 'date'
        }
        return action
