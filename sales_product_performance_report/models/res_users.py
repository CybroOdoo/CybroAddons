# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sabeel B (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.http import request


class ResUsers(models.Model):
    """Inherits the User model for adding fields and methods"""
    _inherit = 'res.users'

    warehouse_id = fields.Many2one('stock.warehouse',
                                   string='Warehouse',
                                   domain="[('company_id', '=', company_id)]")
    estimated_revenue = fields.Float(string="Estimated Revenue",
                                     help='Estimated Revenue of orders done by'
                                          'the user')
    net_revenue = fields.Float(string="Net Revenue",
                               help='Net Revenue of orders')
    total_sale_order = fields.Integer(string="ToTal Order",
                                      help='No of Total Orders')
    sale_order_done = fields.Integer(string="Sale Order Done",
                                     help='No of Done Sale Orders')
    returned_orders = fields.Integer(string="Returned Orders",
                                     help='No of Returned Orders')
    avg_price = fields.Float(string="Avg Price", help='Average Price')
    overall_performance = fields.Float(string="Over All%",
                                       help='Overall Performance')
    overall_performance_separate = fields.Float(string="Over All Separated",
                                                help='Overall Performance of '
                                                     'Sales Person Done with '
                                                     'Different Sales Team')

    def performance_values(self, sale_person, start_date,
                           end_date, up_to_date):
        """
            For Calculate Performance Values
            :param sale_person: for get sale_person .
            :param start_date: for get records after the date .
            :param end_date: for get records before the date.
            :param up_to_date: for up_to_date records.
        """
        domain = [
            ('team_id', '=', self.sale_team_id.id),
            ('user_id', '=', sale_person.id)
        ]
        if not up_to_date:
            if start_date:
                domain.append(('date_order', '>=', start_date))
            if end_date:
                domain.append(('date_order', '<=', end_date))
        sale_order = self.env['sale.order'].search(domain)
        self.total_sale_order = len(sale_order)

        domain.append(('state', '=', 'sale'))
        self.sale_order_done = len(self.env['sale.order'].search(domain))
        self.net_revenue = sum(self.env['sale.order'].search
                               (domain).mapped('amount_total'))
        self.estimated_revenue = sum(sale_order.mapped('amount_total'))
        self.avg_price = self.estimated_revenue / self.total_sale_order \
            if self.total_sale_order else None
        return_order = self.env['stock.picking'].search([
            ('sale_id', 'in', sale_order.ids),
            ('picking_type_id.code', '=', "incoming")
        ])
        self.returned_orders = len(return_order)
        overall_order = self.env['sale.order'].search_count([])
        self.overall_performance = (
                (self.total_sale_order / overall_order) * 100)
        separate_order = self.env['sale.order'].search_count([
            ('team_id', '!=', self.sale_team_id.id),
            ('user_id', '=', sale_person.id)])
        self.overall_performance_separate = (
                (separate_order / overall_order) * 100)

    def action_sale_order(self):
        """
            action for get sale orders done with this product
            return: to sale order tree view and form view
        """
        domain = [('user_id', '=', self.id)]
        if not self._context['up_to_date']:
            if self._context['start_date']:
                domain.append(('date_order', '>=',
                               self._context['start_date']))
            if self._context['end_date']:
                domain.append(('date_order', '<=', self._context['end_date']))
        sale_order = self.env['sale.order'].search(domain).mapped('id')
        tree_view_id = request.env.ref(
            'sale.view_order_tree').id
        form_view_id = request.env.ref(
            'sale.view_order_form').id
        if sale_order:
            return {
                'name': _('Sales Order Report'),
                'res_model': 'sale.order',
                'views': [(tree_view_id, 'list'), (form_view_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'self',
                'domain': [('id', 'in', sale_order) if sale_order else None],
            }
        else:
            raise UserError(_("No Orders done by this Sales Person!"))
