# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class StockMove(models.Model):
    """This class inherits the model stock.move and add the field analytic to
     it, which shows the selected analytic distribution in sale.order.line"""
    _inherit = 'stock.move'

    analytic = fields.Json('Analytic', compute='_compute_analytic',
                           help='Analytic Distribution')
    analytic_precision = fields.Integer(store=False,
                                        help='Define the precision of '
                                             'percentage decimal value',
                                        default=lambda self: self.env[
                                            'decimal.precision'].precision_get(
                                            "Percentage Analytic"))

    def _compute_analytic(self):
        """This function is used to show the selected analytic distribution in
        stock.move """
        for rec in self:
            if rec.sale_line_id:
                analytic_account_id = self.env['sale.order'].search(
                    [('name', '=', rec.origin)]).analytic_account_id.id
                analytic_account = rec.sale_line_id.analytic_distribution
                if analytic_account:
                    analytic_account.update({
                        str(analytic_account_id): 100
                    })
                    rec.analytic = analytic_account
                else:
                    rec.analytic = False
            if rec.purchase_line_id:
                rec.analytic = rec.purchase_line_id.analytic_distribution
