# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (<https://www.cybrosys.com>)
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
###############################################################################
""""
This module is used to add new route /final/customer_rating for adding the
review(comment) and rating from the website.
"""
from odoo import http
from odoo.http import request


class CustomerRatingAndReview(http.Controller):
    """ This class helps to take comment and rating from website. """
    @http.route('/final/customer_rating', type='http', auth="public",
                website=True, sitemap=False)
    def customer_order_rating(self, **kw):
        """ This function helps to fetch the values of comment and rating """
        order_id = request.env['sale.order'].sudo().browse(int(kw['order_id']))
        order_id.comment = kw['comment']
        order_id.rating = kw['rate_value']
        return request.redirect('/shop/confirmation')
