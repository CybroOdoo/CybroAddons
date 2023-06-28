# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
import datetime
from odoo import fields, models


class SaleOrder(models.Model):
    """
    fields included , update values in quotation and conform the quotation
    """
    _inherit = 'sale.order'

    user_description = fields.Text(string="User Description")

    def confirm_delivery_date_schedule(self, data):
        """
        confirm and writing the confirmed quotation
        """
        sale_order = self.env['sale.order'].sudo().browse(int(data['id']))
        sale_order.sudo().update({
            'commitment_date': datetime.datetime.strptime(data['date'],
                                                          "%Y-%m-%d").date(),
            'user_description': data['description']
        })
        sale_order.sudo().action_confirm()
