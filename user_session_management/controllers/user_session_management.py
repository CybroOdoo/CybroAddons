# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith PG (odoo@cybrosys.com)
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
from user_agents import parse
from odoo import http
from odoo.http import request
from odoo.fields import Datetime
from odoo.addons.web.controllers.main import Home, Session


class Home(Home):
    """Subclass of Home which creates the session data in User Session Login.
    When a user logs in successfully, a record is created in the
    'user.session.login' with information about the user's session, device,
    browser, and IP address.
    """
    @http.route()
    def web_login(self, redirect=None, **kw):
        """
        Overrides the web_login method of Home to create a
        user session login record when a user logs in successfully.
        """
        res = super().web_login(redirect=redirect, **kw)
        if request.params['login_success']:
            user = request.env['res.users'].sudo().search(
                [('login', '=', kw['login'])], limit=1)
            if user:
                user.status = 'done'
                agent = request.httprequest.environ.get('HTTP_USER_AGENT')
                user_agent = parse(agent)
                request.env['user.session.login'].create({
                    'status': 'done',
                    'user_id': user.id,
                    'sid': request.session.sid,
                    'login_date': Datetime.now(),
                    'device': user_agent.get_device(),
                    'os': user_agent.os.family,
                    'browser': user_agent.browser.family,
                    'ip_address': request.httprequest.environ['REMOTE_ADDR'],
                    'state': 'active'
                })
        return res


class Session(Session):
    """Subclass of the Session used to update the user session login record
    when a user logs out.
    """
    @http.route()
    def logout(self, redirect='/web', uid=False, usm_session_id=False):
        """Updates the logout status"""
        user = request.env['res.users'].sudo().browse(
            [uid or request.session.uid])
        if user:
            loggedout = request.env['user.session.login'].sudo().search(
                [('user_id', '=', user.id), ('logout_date', '=', False),
                 ('id', '=', usm_session_id or request.session.usm_session_id)],
                limit=1)
            if loggedout:
                loggedout.logout_date = Datetime.now()
                loggedout.update({
                    'status': 'blocked',
                    'state': 'closed'
                })
            # Updating status indicator
            state_mapped = request.env['user.session.login'].sudo().search(
                [('user_id', '=', user.id)]).mapped('state')
            if 'active' not in state_mapped:
                user.status = 'blocked'
        return super().logout(redirect=redirect)
