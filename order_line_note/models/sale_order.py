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
from odoo import models


class SaleOrder(models.Model):
    """This class extends the 'sale.order' model to customize the behavior of
     confirming sale orders."""
    _inherit = 'sale.order'

    def action_confirm(self):
        """This method extends the base 'action_confirm' method to copy notes
        from sale order lines to related stock moves."""
        res = super().action_confirm()
        for rec in self.order_line:
            self.env['stock.move'].search([('sale_line_id', '=', rec.id)])[
                'note'] = rec.note
        return res
