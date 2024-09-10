# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Juman Haseen (<https://www.cybrosys.com>)
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


class WebsiteCountry(http.Controller):
    """
        This controller used to pass the selected country to the corresponding
        template
    """
    @http.route('/website/countries', type='json', auth="user", website=True)
    def website_languages(self, country_id):
        """
        This function used to search the country id, and it renders the
        details of the selected country in to the template.
        """
        country_id = request.env['res.country'].browse(int(country_id))
        website_id = request.env['website'].browse(request.website.id)
        website_id.default_country_id = country_id.id

        response = {
            'country_name': country_id.name,
            'country_image_url': country_id.image_url,
            'country_code': country_id.code
        }
        return response
