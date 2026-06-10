# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request

class RecommendationController(http.Controller):

    @http.route('/recommendation/session/get', type='json', auth='user', methods=['POST'])
    def get_session_recommendations(self):
        """Return recommendations safely for logged-in user."""
        user = request.env.user.sudo()
        return user.recommended_products_data or []

    @http.route('/recommendation/session/save', type='json', auth='user', methods=['POST'])
    def save_session_recommendations(self, products):
        """Save updated recommendations."""
        user = request.env.user.sudo()
        user.write({"recommended_products_data": products})
