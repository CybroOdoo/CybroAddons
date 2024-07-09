# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nihala KP (<https://www.cybrosys.com>)
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


class UserSwitch(http.Controller):
    """This is a controller to switch user and switch back to admin
        user_switch:
            this function is to check weather the user is admin or not
        switch_admin:
            function to switch back to admin
    """
    @http.route('/switch/admin', type='json', auth='public')
    def switch_admin(self):
        """
            Summary:
                Function to move back to admin
            Return:
                The home page to be loaded
                """
        session = request.session
        pre_user = request.env['res.users'].browse(session.previous_user)
        if pre_user and pre_user._is_admin:
            session.authenticate_without_password(request.env.cr.dbname,
                                                  pre_user.login, request.env)
            return {
                'type': 'ir.actions.act_url',
                'url': '/',
                'target': 'self'
            }
        return True
