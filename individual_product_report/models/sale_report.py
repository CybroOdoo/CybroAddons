# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, fields, api


class SaleProductTemplateReport(models.Model):
    _inherit = 'product.template'

    def action_view_sales_report(self):
        """ To view the graph view on click of Sales Report Button in product.template model """

        action = self.env.ref('individual_product_report.report_sales_product_graph').read()[0]
        action['domain'] = [('product_tmpl_id', 'in', self.ids)]
        action['context'] = {
            'graph_measure': ['product_uom_qty'],
            'active_id': self._context.get('active_id'),
            'active_model': 'sale.report',
            'search_default_Sales': 1,
            'time_ranges': {'field': 'date', 'range': 'last_365_days'},
            'group_by': 'date',
        }
        return action


class SaleProductReport(models.Model):
    _inherit = 'product.product'

    def action_view_sales_report(self):
        """ To view the graph view on click of Sales Report Button in product.product model """

        action = self.env.ref('individual_product_report.report_sales_product_graph').read()[0]
        action['domain'] = [('product_id', 'in', self.ids)]
        action['context'] = {
            'graph_measure': ['product_uom_qty'],
            'active_id': self._context.get('active_id'),
            'active_model': 'sale.report',
            'search_default_Sales': 1,
            'time_ranges': {'field': 'date', 'range': 'last_365_days'},
            'group_by': 'date',
        }
        return action
