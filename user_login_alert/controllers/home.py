# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from time import gmtime, strftime
import odoo
import odoo.modules.registry

try:
    import httpagentparser
except ImportError:
    pass
from odoo import http
from odoo.tools.translate import _
from odoo.http import request
from odoo.addons.web.controllers import home


class Home(home.Home):
    """Inherit Home to add features login page"""

    @http.route(route='/web/login', type='http', auth="public")
    def web_login(self, redirect=None, **kw):
        """Method that check if user login in any system firstly,
            an email will send to user related partner's mail. """
        home.ensure_db()
        request.params['login_success'] = False
        if (request.httprequest.method == 'GET' and redirect
                and request.session.uid):
            return request.redirect(redirect)
        if not request.uid:
            request.uid = odoo.SUPERUSER_ID
        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        if request.httprequest.method == 'POST':
            uid = request.session.authenticate(request.session.db,
                                               request.params['login'],
                                               request.params['password'])
            if uid is not False:
                user_rec = request.env['res.users'].sudo().browse(uid)
                request.params['login_success'] = True
                if user_rec.partner_id.email and user_rec.has_group(
                        'user_login_alert.receive_login_notification'):
                    agent_details = httpagentparser.detect(request.httprequest.
                                                           environ.get(
                                                            'HTTP_USER_AGENT'))
                    user_os = agent_details['os']['name']
                    browser_name = agent_details['browser']['name']
                    ip_address = request.httprequest.environ['REMOTE_ADDR']
                    if (user_rec.last_logged_ip and user_rec.last_logged_browser
                            and user_rec.last_logged_os):
                        if (user_rec.last_logged_ip != ip_address or
                                user_rec.last_logged_browser != browser_name or
                                user_rec.last_logged_os != user_os):
                            send_mail = 1
                            user_rec.last_logged_ip = ip_address
                            user_rec.last_logged_browser = browser_name
                            user_rec.last_logged_os = user_os
                        else:
                            send_mail = 0
                    else:
                        send_mail = 1
                        user_rec.last_logged_ip = ip_address
                        user_rec.last_logged_browser = browser_name
                        user_rec.last_logged_os = user_os
                    if send_mail == 1:
                        request.env['mail.mail'].sudo().create(
                            {'subject': 'Login Alert : ' +
                                        strftime("%Y-%m-%d %H:%M:%S",
                                                 gmtime()),
                             'body_html': ('Hi ' + user_rec.name +
                                           ' , Your account has been '
                                           'accessed successfully. The '
                                           'details of the system from which'
                                           ' the account is accessed ..., '
                                           '<table border="1" width="100%" '
                                           'cellpadding="0" '
                                           'bgcolor="#ededed"> <tr><td>' +
                                           'OS' + '</td><td>' + user_os +
                                           '</td></tr><tr><td>' + 'Browser' +
                                           '</td><td>' + browser_name +
                                           '</td></tr><tr><td>' + 'IP Address'
                                           + '</td><td>' + ip_address
                                           + '</td></tr> </table> Thank you'),
                             'email_from': request.env.user.company_id.email,
                             'email_to': user_rec.partner_id.email
                             }
                        ).send()
                if not redirect:
                    redirect = '/web'
                return request.redirect(
                    self._login_redirect(uid, redirect=redirect))
            values['error'] = _("Wrong login/password")
        return request.render('web.login', values)
