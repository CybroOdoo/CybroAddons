# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu K P (odoo@cybrosys.com)
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
################################################################################
from odoo import http
from odoo.http import request
import werkzeug
from odoo.addons.web.controllers.main import home


class PosScreen(home.Home):
    """The class PosScreen is used to log in pos session directly"""

    @http.route('/web/login', type='http', auth="public", website=True,
                sitemap=False)
    def web_login(self, redirect=None, **kw):
        """Override to add direct login to POS"""
        res = super().web_login(redirect=redirect, **kw)
        if request.env.user.pos_conf_id:
            if not request.env.user.pos_conf_id.current_session_id:
                request.env['pos.session'].sudo().create({
                    'user_id': request.env.uid,
                    'config_id': request.env.user.pos_conf_id.id
                })
            return werkzeug.utils.redirect('/pos/ui')
        return res
