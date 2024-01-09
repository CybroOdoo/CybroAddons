# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (<https://www.cybrosys.com>)
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
###############################################################################
import hashlib
import odoo
from odoo import http
from odoo.tools import pycompat
from odoo.tools.translate import _
from odoo.http import request
from odoo.addons.web.controllers.home import Home as WebHome
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url

# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error',
                          'scope', 'mode', 'redirect', 'redirect_hostname',
                          'email', 'name', 'partner_id', 'password',
                          'confirm_password', 'city', 'country_id', 'lang'}


class Home(WebHome):
    @http.route(route='/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        """Override web_login function to add features of this module."""
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)
        if not request.uid:
            request.update_env(user=odoo.SUPERUSER_ID)
        values = {val: item for val, item in request.params.items() if
                  val in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.update_env(user=request.session.uid)

            try:
                uid = request.session.authenticate(request.session.db,
                                                   request.params['login'],
                                                   request.params['password'])
                request.params['login_success'] = True
                return request.redirect(
                    self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                request.update_env = old_uid
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get(
                    'error') == 'access':
                values['error'] = _(
                    'Only employees can access this database. '
                    'Please contact the administrator.')
        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')
        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True
        conf_param = request.env['ir.config_parameter'].sudo()
        orientation = conf_param.get_param('web_login_styles.orientation')
        image = conf_param.get_param('web_login_styles.image')
        url = conf_param.get_param('web_login_styles.url')
        background_type = conf_param.get_param('web_login_styles.background')
        if background_type == 'color':
            values['bg'] = ''
            values['color'] = conf_param.sudo().get_param(
                'web_login_styles.color')
        elif background_type == 'image':
            exist_rec = request.env['ir.attachment'].sudo().search(
                [('is_background', '=', True)])
            if exist_rec:
                exist_rec.unlink()
            attachments = request.env['ir.attachment'].sudo().create({
                'name': 'Background Image',
                'datas': image,
                'type': 'binary',
                'mimetype': 'image/png',
                'public': True,
                'is_background': True
            })
            base_url = conf_param.sudo().get_param('web.base.url')
            url = base_url + '/web/image?' + 'model=ir.attachment&id=' + str(
                attachments.id) + '&field=datas'
            values['bg_img'] = url or ''
        elif background_type == 'url':
            pre_exist = request.env['ir.attachment'].sudo().search(
                [('url', '=', url)])
            if not pre_exist:
                attachments = request.env['ir.attachment'].sudo().create({
                    'name': 'Background Image URL',
                    'url': url,
                    'type': 'url',
                    'public': True
                })
            else:
                attachments = pre_exist
            encode = hashlib.md5(
                pycompat.to_text(attachments.url).encode("utf-8")).hexdigest()[
                     0:7]
            encode_url = "/web/image/{}-{}".format(attachments.id, encode)
            values['bg_img'] = encode_url or ''
        if orientation == 'right':
            response = request.render('web_login_styles.login_template_right',
                                      values)
        elif orientation == 'left':
            response = request.render('web_login_styles.login_template_left',
                                      values)
        elif orientation == 'middle':
            response = request.render('web_login_styles.login_template_middle',
                                      values)
        else:
            response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
