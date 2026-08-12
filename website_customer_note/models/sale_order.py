# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class SaleOrderInherited(models.Model):
    """Inherit sale orders to store customer notes from the website."""

    _inherit = 'sale.order'

    customer_note = fields.Text(string="Customer Note")

    @api.model
    def write_customer_note(self, sale_order_id, customer_note):
        """
        Write customer note to a sale order.

        :param sale_order_id: ID of the sale order to which the customer note is to be written.
        :type sale_order_id: int
        :param customer_note: Text of the customer note.
        :type customer_note: str
        :return: True if successfully written, False otherwise.
        :rtype: bool
        """
        sale_order = self.env['sale.order'].browse(sale_order_id)
        sale_order.write({'customer_note': customer_note})
        return True
