# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(odoo@cybrosys.com)
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



from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteComment(WebsiteSale):

    """Add Customer comment functions to the website_sale controller."""
    @http.route(['/shop/customer_comment'], type='json', auth="public", methods=['POST'], website=True)
    def customer_comment(self, **data):
        """ Json method that used to add a
        comment when the user clicks on 'pay now' button.
        """
        if data.get('comment'):
            order = request.website.sale_get_order()
            redirect = self.checkout_redirection(order)
            if redirect:
                return redirect

            if order and order.id:
                order.write({'comment': data.get('comment')})

        return True
