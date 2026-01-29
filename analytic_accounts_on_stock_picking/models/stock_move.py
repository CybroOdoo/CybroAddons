# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
##############################################################################
from odoo import fields, models


class StockMove(models.Model):
    """ This class inherits the model 'stock.move' and add the field analytic,
    which shows the selected analytic distribution in 'sale.order.line'. """
    _inherit = 'stock.move'

    analytic = fields.Text('Analytic Account', compute='_compute_analytic',
                           help='Analytic Distribution')
    analytic_precision = fields.Integer(
        store=False,
        default=lambda self: self.env['decimal.precision'].precision_get(
            "Percentage Analytic"),
        help='Define the precision of percentage decimal value')

    def _compute_analytic(self):
        """ This function is used to show the selected analytic distribution in
        'stock.move'. """
        analytic_accounts = []
        for rec in self:
            if rec.sale_line_id:
                sale_order = self.env['sale.order'].search(
                    [('name', '=', rec.origin)])
                if sale_order:
                    rec.analytic = rec.sale_line_id.analytic_account_id.name
            if rec.purchase_line_id:
                rec.analytic = rec.purchase_line_id.account_analytic_id.name
        if analytic_accounts:
            for rec in self:
                rec.analytic = [i for i in set(analytic_accounts)]
