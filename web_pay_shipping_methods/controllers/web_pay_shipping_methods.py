# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

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
from odoo import http
from odoo.http import request


class PaymentAcquirer(http.Controller):
    """ Controller for adding corresponding delivery method of the
        payment provider"""

    @http.route('/get/shipping/methods', type="json", auth="public",
                website=True)
    def get_shipping_methods(self, args):
        """args: Contains the id of the payment provider selected from website.
        Returns the delivery_carrier ids specified inside the payment
        provider."""
        return [rec.id for rec in request.env['payment.provider'].sudo().browse(
            int(args)).delivery_carrier_ids]
