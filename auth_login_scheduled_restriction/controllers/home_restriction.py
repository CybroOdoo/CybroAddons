# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
from odoo.addons.web.controllers import home
from odoo.addons.web.controllers.utils import ensure_db
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class Home(home.Home):
    """Custom Home class for handling web login with working hours restriction.

    Extends the base Home class to enforce login restrictions based on
    configured working hours per user.
    """

    @http.route()
    def web_login(self, *args, **kw):
        """Handle web login with login restriction checks.

        Validates that the user is attempting to login during their
        configured working hours before allowing access.
        """
        ensure_db()
        try:
            response = super(Home, self).web_login(*args, **kw)
            # If login was successful (POST request and user is authenticated)
            if request.env.uid and request.httprequest.method == 'POST':
                user = request.env['res.users'].browse(request.env.uid)
                try:
                    user.check_login_restrictions()
                except AccessDenied as e:
                    # Clear session on restriction
                    request.session.logout()
                    _logger.warning(
                        f"Login attempt denied for user {user.login} "
                        f"outside working hours: {str(e)}"
                    )
                    # Return login page with error message
                    return self._render_login_page(
                        error=str(e),
                        **kw
                    )
            return response
        except AccessDenied as e:
            _logger.warning(f"Login restriction error: {str(e)}")
            # Return to login page with error
            return self._render_login_page(
                error=str(e),
                **kw
            )

    def _render_login_page(self, error=None, **kw):
        """Render the login page with optional error message.

        Args:
            error (str): Error message to display
            **kw: Additional keyword arguments to pass to parent

        Returns:
            Response with rendered login page
        """
        return super(Home, self).web_login(
            error=error,
            **kw
        )
