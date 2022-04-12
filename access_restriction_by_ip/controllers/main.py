# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Niyas Raphy(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.addons.web.controllers.main import Home
from odoo.http import request
from odoo.exceptions import Warning
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http
import ipaddress


SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang'}


class IPRestriction(Home):

    @http.route()
    def web_login(self, *args, **kwargs):
        request.params['login_success'] = False
        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            ip_address = request.httprequest.environ['REMOTE_ADDR']
            login_ip = ipaddress.ip_network(ip_address)
            user_rec = request.env['res.users'].sudo().search([('login', '=', request.params.get('login', False))])
            if user_rec.allowed_ips:
                ip_ok = False
                for rec in user_rec.allowed_ips:
                    if login_ip.subnet_of(ipaddress.ip_network(rec.ip_address, False)):
                        ip_ok = True
                        break

                if not ip_ok:
                    request.uid = old_uid
                    values['error'] = _("Not allowed to login from this IP (%s)" % ip_address)

                    if not odoo.tools.config['list_db']:
                        values['disable_database_manager'] = True

                    response = request.render('web.login', values)
                    response.headers['X-Frame-Options'] = 'DENY'
                    return response

        return super(IPRestriction, self).web_login(*args, **kwargs)
