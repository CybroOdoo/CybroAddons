# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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


class SaleOrderLine(models.Model):
    """Inherited sale.order.line to add field"""
    _inherit = 'sale.order.line'

    note = fields.Char(string='Note', help='Add note for product')

    def _prepare_invoice_line(self, **optional_values):
        """This method is called to prepare the values required for creating
        an invoice line based on the sale order line."""
        res = super(SaleOrderLine,self)._prepare_invoice_line(**optional_values)
        res['note'] = self.note
        return res
