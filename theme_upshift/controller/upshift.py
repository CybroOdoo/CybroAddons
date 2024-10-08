# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: FATHIMA SHALFA P (odoo@cybrosys.com)
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
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class MenuController(http.Controller):
    """
    Controller for handling redirections to various pages based on menu clicks.

    This class defines several routes that redirect users to different pages
    in the website based on the menus clicked. Each method corresponds to a specific
    page in the 'theme_upshift' theme.

    """

    @http.route('/home', website=True, type='http', auth='public',csrf=False)
    def home_page(self):
        """Redirect to the home page."""
        return request.render('theme_upshift.upshift_home_page')

    @http.route('/contact-us', website=True, type='http', auth='public',
                csrf=False)
    def contact_us(self):
        """Redirect to the contact us page."""
        return request.render('theme_upshift.upshift_contact_us')

    @http.route('/thank_you_page', website=True, type='http', auth='public',
                csrf=False)
    def thank_you(self):
        """Redirect to the Thank you page."""
        return request.render('theme_upshift.thank_you_page')

    @http.route('/about', website=True, type='http', auth='public',
                csrf=False)
    def about_page(self):
        """Redirect to the about page."""
        return request.render('theme_upshift.about_page')

    @http.route('/project', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_project(self):
        """Redirect to the portfolio project page."""
        return request.render('theme_upshift.portfolio_project')

    @http.route('/another_action', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_another_action(self):
        """Redirect to the portfolio Another Action page."""
        return request.render('theme_upshift.portfolio_another_action')

    @http.route('/another_action2', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_another_action2(self):
        """Redirect to the portfolio Another Action page 2."""
        return request.render('theme_upshift.portfolio_another_action2')

    @http.route('/another_action3', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_another_action3(self):
        """Redirect to the portfolio Another Action page 3."""
        return request.render('theme_upshift.portfolio_another_action3')

    @http.route('/another_action4', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_another_action4(self):
        """Redirect to the portfolio Another Action page 4."""
        return request.render('theme_upshift.portfolio_another_action4')

    @http.route('/another_action5', website=True, type='http', auth='public',
                csrf=False)
    def portfolio_another_action5(self):
        """Redirect to the portfolio Another Action page 5."""
        return request.render('theme_upshift.portfolio_another_action5')

    @http.route('/another_action6', website=True, type='http', auth='public',
            csrf=False)
    def portfolio_another_action6(self):
        """Redirect to the portfolio Another Action page 6."""
        return request.render('theme_upshift.portfolio_another_action6')
