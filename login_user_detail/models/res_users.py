# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models
from odoo.http import request


class ResUsers(models.Model):
    """ Inherits 'res.users' to add custom functionality for logging the login
    details of user. """
    _inherit = 'res.users'

    def _login(self, credential, user_agent_env):
        """ Log the user name and IP address of every successful login.
        Overrides _login rather than _check_credentials, which also runs for
        password re-confirmations and RPC calls that are not logins. """
        auth_info = super()._login(credential, user_agent_env)
        user = self.env['res.users'].sudo().browse(auth_info['uid'])
        ip_address = (request.httprequest.environ.get('REMOTE_ADDR', '')
                      if request else '')
        self.env['login.detail'].sudo().create({
            'user_id': user.id,
            'name': user.name,
            'ip_address': ip_address,
        })
        return auth_info
