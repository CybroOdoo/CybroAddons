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


class LunchOrderReport(models.AbstractModel):
    """Model for creating custom reports. Passing the values to the template"""
    _name = 'report.lunch_order_pdf.report_lunch_order'
    _description = 'Report for lunch orders'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Override the method to create custom report with custom values
        :param docids: the recordset/ record from which the report action is
        invoked
        :param data: report data
        :return: data dictionary to pass values to the report template
        """
        period = None
        grouped_orders = []
        if docids:
            docs = self.env['lunch.report'].browse(docids)
        elif self.env.context.get('active_ids'):
            docs = self.env['lunch.report'].browse(self.env.context.get('active_ids'))
        elif self.env.context.get('active_id'):
            docs = self.env['lunch.report'].browse(self.env.context.get('active_id'))
        else:
            docs = self.env['lunch.report'].browse()
        lang = self.env['res.lang'].search(
            [('code', '=', self.env.context.get('lang'))])
        order_ids = data.get('order_ids', []) if data else []
        orders = self.env['lunch.order'].sudo().browse(order_ids)
        end_date = docs.end_date if docs else fields.Date.context_today(self)
        if not end_date:
            end_date = fields.Date.context_today(self)
        if docs and docs.start_date:
            date_format = lang.date_format if lang else '%m/%d/%Y'
            period = "From " + docs.start_date.strftime(
                date_format) + " To " + end_date.strftime(date_format)
        if docs.group_order:
            if docs.group_order == 'user_id':
                users = orders.mapped('user_id').sorted(key='name')
                for user in users:
                    grouped_orders.append([user.name, orders.filtered(
                        lambda order: order.user_id == user)])
            elif docs.group_order == 'supplier_id':
                vendors = orders.mapped('supplier_id').sorted(key='name')
                for vendor in vendors:
                    grouped_orders.append([vendor.name, orders.filtered(
                        lambda order: order.supplier_id == vendor)])
            elif docs.group_order == 'product_id':
                products = orders.mapped('product_id').sorted(key='name')
                for product in products:
                    grouped_orders.append([product.name, orders.filtered(
                        lambda order: order.product_id == product)])
            elif docs.group_order == 'state':
                order_states = ['new', 'ordered', 'confirmed', 'cancelled']
                states = orders.mapped('state')
                for state in order_states:
                    if state in states:
                        grouped_orders.append([state, orders.filtered(
                            lambda order: order.state == state)])
            else:
                companies = orders.mapped('company_id').sorted(key='name')
                for company in companies:
                    grouped_orders.append([company.name, orders.filtered(
                        lambda order: order.company_id == company)])
        else:
            grouped_orders.append([False, orders])
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'group_order': docs.group_order if docs else False,
            'grouped_orders': grouped_orders,
            'period': period
        }
