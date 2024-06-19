# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Aslam A K( odoo@cybrosys.com )
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json
from odoo import http
from odoo.http import request


class OnedriveAuth(http.Controller):
    """
    Return URL
    """

    @http.route('/onedrive/authentication', type='http', auth="public")
    def oauth2callback(self, **kw):
        """
        Return URL
        """
        state = json.loads(kw['state'])
        onedrive_config_id = request.env['onedrive.dashboard'].sudo().browse(
                             state.get('onedrive_config_id'))
        onedrive_config_id.get_tokens(kw.get('code'))
        return request.redirect(state.get('url_return'))
