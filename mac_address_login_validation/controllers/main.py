# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-November Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
import sys
import subprocess
from odoo.addons.web.controllers import home
from odoo.http import request
from odoo.exceptions import Warning
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http

_logger = logging.getLogger(__name__)
py_v = "python%s.%s" % (sys.version_info.major, sys.version_info.minor)

try:
    from getmac import get_mac_address as gma
except ImportError:
    _logger.info('\n There was no such module named -getmac- installed')
    _logger.info('xxxxxxxxxxxxxxxx installing getmac xxxxxxxxxxxxxx')
    subprocess.check_call([py_v, "-m", "pip", "install", "getmac"])
    from getmac import get_mac_address as gma


class Home(home.Home):

    @http.route('/web/login', type='http', auth="public")
    def web_login(self, redirect=None, **kw):
        home.ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID
        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        if request.httprequest.method == 'POST':
            old_uid = request.uid
            mac_address = gma()
            if request.params['login']:
                user_rec = request.env['res.users'].sudo().search(
                    [('login', '=', request.params['login'])])
                if user_rec.mac_address_login_toggle:
                    mac_address_list = []
                    for rec in user_rec.mac_address_ids:
                        mac_address_list.append(rec.mac_address)
                    if mac_address in mac_address_list:
                        try:
                            uid = request.session.authenticate(
                                request.session.db,
                                request.params[
                                    'login'],
                                request.params[
                                    'password'])
                            request.params['login_success'] = True
                            return request.redirect(
                                self._login_redirect(uid, redirect=redirect))
                        except odoo.exceptions.AccessDenied as e:
                            request.uid = old_uid
                            if e.args == odoo.exceptions.AccessDenied().args:
                                values['error'] = _("Wrong login/password")

                    else:
                        request.update_env(user=old_uid)
                        values['error'] = _(
                            "Not allowed to login from this Device")
                else:
                    try:
                        uid = request.session.authenticate(request.session.db,
                                                           request.params[
                                                               'login'],
                                                           request.params[
                                                               'password'])
                        request.params['login_success'] = True

                        return request.redirect(
                            self._login_redirect(uid, redirect=redirect))
                    except odoo.exceptions.AccessDenied as e:
                        request.uid = old_uid
                        if e.args == odoo.exceptions.AccessDenied().args:
                            values['error'] = _("Wrong login/password")

        return request.render('web.login', values)
