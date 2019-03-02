# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
###################################################################################

import odoo
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import Home, ensure_db


class AutoDeveloperMode(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        """ Controller functions overrides for redirecting to developer mode if the logging user is admin or
         'Odoo Developer' group member """
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            print("uid",uid)
            if uid is not False:
                request.params['login_success'] = True
                if not redirect:
                    odoo_technician = request.env.user.has_group('developer_mode.odoo_developer_group')
                    
                    if odoo_technician or request.uid == True:
                        redirect = '/web?debug'
                    else:
                        redirect = '/web'
                return http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['error'] = _("Wrong login/password")
        return request.render('web.login', values)
