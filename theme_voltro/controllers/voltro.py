# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class MenuController(http.Controller):
    """
    Controller for handling redirections to various pages based on menu clicks.

    This class defines several routes that redirect users to different pages
    in the website based on the menus clicked. Each method corresponds to a specific
    page in the 'theme_voltro' theme.

    """

    @http.route('/about', website=True, type='http', auth='public',csrf=False)
    def home_page(self):
        """Redirect to the about page."""
        return request.render('theme_voltro.about_page')
