# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

import json

from odoo import http
from odoo.http import request


class OnedriveAuth(http.Controller):

    @http.route('/onedrive/authentication', type='http', auth="public")
    def oauth2callback(self, **kw):
        state = json.loads(kw['state'])
        backup_config = request.env['db.backup.configure'].sudo().browse(state.get('backup_config_id'))
        backup_config.get_onedrive_tokens(kw.get('code'))
        url_return = state.get('url_return')
        return request.redirect(url_return)

    @http.route('/google_drive/authentication', type='http', auth="public")
    def gdrive_oauth2callback(self, **kw):
        state = json.loads(kw['state'])
        backup_config = request.env['db.backup.configure'].sudo().browse(state.get('backup_config_id'))
        backup_config.get_gdrive_tokens(kw.get('code'))
        url_return = state.get('url_return')
        return request.redirect(url_return)
