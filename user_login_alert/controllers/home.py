# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
# -*- coding: utf-8 -*-
from time import gmtime, strftime
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home as WebHome

try:
    import httpagentparser
except ImportError:
    httpagentparser = None


class Home(WebHome):
    """Inherit Home to add login notification alert"""

    @http.route()
    def web_login(self, redirect=None, **kw):
        response = super().web_login(redirect=redirect, **kw)

        # Check if the user successfully logged in
        if request.params.get('login_success') and request.session.uid:
            uid = request.session.uid
            user_rec = request.env['res.users'].sudo().browse(uid)
            if user_rec.partner_id.email and user_rec.has_group(
                    'user_login_alert.receive_login_notification'):
                agent_details = (
                    httpagentparser.detect(
                        request.httprequest.environ.get('HTTP_USER_AGENT', ''))
                    if httpagentparser else {'os': {'name': 'Unknown'},
                                             'browser': {'name': 'Unknown'}}
                )
                user_os = agent_details.get('os', {}).get('name', 'Unknown')
                browser_name = agent_details.get('browser', {}).get('name',
                                                                    'Unknown')
                ip_address = request.httprequest.environ.get('REMOTE_ADDR', '')

                send_mail = False
                if user_rec.last_logged_ip and user_rec.last_logged_browser and user_rec.last_logged_os:
                    if (user_rec.last_logged_ip != ip_address or
                            user_rec.last_logged_browser != browser_name or
                            user_rec.last_logged_os != user_os):
                        send_mail = True
                else:
                    send_mail = True

                if send_mail:
                    user_rec.last_logged_ip = ip_address
                    user_rec.last_logged_browser = browser_name
                    user_rec.last_logged_os = user_os
                    request.env['mail.mail'].sudo().create({
                        'subject': f"Login Alert : {strftime('%Y-%m-%d %H:%M:%S', gmtime())}",
                        'body_html': (
                            f"Hi {user_rec.name}, Your account has been accessed successfully. "
                            "The details of the system from which the account is accessed:<br/>"
                            '<table border="1" width="100%" cellpadding="4" bgcolor="#ededed">'
                            f"<tr><td><b>OS</b></td><td>{user_os}</td></tr>"
                            f"<tr><td><b>Browser</b></td><td>{browser_name}</td></tr>"
                            f"<tr><td><b>IP Address</b></td><td>{ip_address}</td></tr>"
                            "</table><br/>Thank you"
                        ),
                        'email_from': request.env.company.email or request.env.user.company_id.email,
                        'email_to': user_rec.partner_id.email,
                    }).send()

        return response

