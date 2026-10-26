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
#############################################################################
from odoo import http
from odoo.http import request


class AutoLogoutIdleUser(http.Controller):
    """Controller to provide idle timeout settings for the logged-in user."""

    @http.route('/auto_logout_idle_user_odoo/idle_time', auth='user', type='jsonrpc')
    def get_idle_time(self):
        """Return the idle timeout (in minutes) of the current user.

        The result is a dict with the key ``idle_time`` which is 0 when the
        idle timeout is not enabled for the user.
        """
        user = request.env.user
        if user.enable_idle and user.idle_time > 0:
            return {'idle_time': user.idle_time}
        return {'idle_time': 0}
