# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LunchReport(models.TransientModel):
    """Creating the report for Lunch"""
    _name = 'lunch.report'
    _description = 'Wizard for lunch report'

    start_date = fields.Date(
        string='Start Date', required=True, default=fields.Date.context_today,
        help='Start date to filter the records')
    end_date = fields.Date(
        string='End Date', default=fields.Date.context_today,
        help='End date to filter the records')
    user_ids = fields.Many2many('res.users', string='Users',
                                domain='[("share", "=", False)]',
                                help="Add user for filter based on user")
    lunch_supplier_ids = fields.Many2many('lunch.supplier', string='Vendors',
                                          help='Vendors/ Lunch Suppliers.')
    lunch_location_ids = fields.Many2many(
        'lunch.location', string='Lunch Locations',
        help="The Locations allocated for lunch")
    product_filter = fields.Selection(
        [('product', 'Product'), ('category', 'Product Category')],
        string='Product Filter',
        help='Filter orders by Products or Product Categories.')
    product_ids = fields.Many2many(
        'lunch.product', string='Products',
        domain='[("active", "=", True)]', help='Products belongs to lunch')
    category_ids = fields.Many2many(
        'lunch.product.category', string='Categories',
        help='Lunch Product Categories.')
    company_ids = fields.Many2many('res.company', string='Companies',
                                   help='For selecting the Companies')
    group_order = fields.Selection(
        [('user_id', 'User'), ('supplier_id', 'Vendor'),
         ('product_id', 'Product'), ('state', 'Status'),
         ('company_id', 'Company')], string='Group Orders',
        help='Group orders in the report')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        """
        Set valid start_date on changing it
        """
        if not self.end_date:
            if self.start_date and self.start_date > fields.Date.context_today(
                    self):
                self.start_date = fields.Date.context_today(self)
        else:
            if self.start_date and self.start_date > self.end_date:
                self.start_date = self.end_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        """
        Set valid end_date on changing it
        """
        if self.start_date and self.end_date and \
                self.start_date > self.end_date:
            self.end_date = self.start_date
        if self.end_date and self.end_date > fields.Date.context_today(self):
            self.end_date = fields.Date.context_today(self)

    def action_print_report(self):
        """
        Print PDF report for lunch based on selected data
        :return: report action
        """
        domain = [('date', '>=', self.start_date)]
        if self.end_date:
            domain += [('date', '<=', self.end_date)]
        if self.user_ids:
            domain += [('user_id', 'in', self.user_ids.ids)]
        if self.company_ids:
            domain += [('company_id', 'in', self.company_ids.ids)]
        if self.lunch_supplier_ids:
            domain += [('supplier_id', 'in', self.lunch_supplier_ids.ids)]
        if self.lunch_location_ids:
            domain += [('lunch_location_id', 'in', self.lunch_location_ids.ids)]
        if self.product_filter == 'product' and self.product_ids:
            domain += [('product_id', 'in', self.product_ids.ids)]
        if self.product_filter == 'category' and self.category_ids:
            domain += [('product_id.category_id', 'in', self.category_ids.ids)]
        orders = self.env['lunch.order'].sudo().search(domain)
        if not orders:
            raise UserError(_('There are no lunch orders in this period!'))
        data = {'order_ids': orders.ids}
        return self.env.ref(
            'lunch_order_pdf.report_lunch_report_action').report_action(
            self, data=data)
