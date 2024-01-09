# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models


class PaymentAcquirer(models.Model):
    """Inherited payment_provider to add shipping method field"""
    _inherit = 'payment.acquirer'

    delivery_carrier_ids = fields.Many2many('delivery.carrier',
                                            string="Shipping Methods",
                                            domain="[('website_published',"
                                                   " '=', True)]",
                                            help="Add shipping methods which "
                                                 "will be available while "
                                                 "choosing this payment "
                                                 "provider")

    @api.model
    def get_shipping_methods(self, args):
        """Search the delivery carriers defined inside payment provider which
        is clicked from website.
        :param str args: id of the clicked payment provider
        :return: recordset of the delivery carriers.
        """
        data = []
        delivery_method_ids =\
            self.sudo().browse(int(args)).delivery_carrier_ids
        for rec in delivery_method_ids:
            data.append(rec.id)
        return data
