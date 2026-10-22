# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    """Inherits the model ir.http to enforce developer mode restrictions and
    pass group information to session_info"""
    _inherit = 'ir.http'

    @classmethod
    def _handle_debug(cls):
        super()._handle_debug()
        if request and request.session.uid and request.env.user:
            if request.env.user.has_group('restrict_web_debug.restrict_debug_mode'):
                request.session.debug = ''

    @classmethod
    def _pre_dispatch(cls, rule, args):
        super()._pre_dispatch(rule, args)
        if request and request.session.uid and request.env.user:
            if request.env.user.has_group('restrict_web_debug.restrict_debug_mode'):
                request.session.debug = ''

    def session_info(self):
        """This is used to get the session user's group information and enforce debug restriction"""
        user_is_restricted = self.env.user.has_group(
            'restrict_web_debug.restrict_debug_mode'
        )
        if user_is_restricted and request and request.session:
            request.session.debug = ''
        info = super().session_info()
        info["user_group"] = user_is_restricted
        if user_is_restricted and 'bundle_params' in info and 'debug' in info['bundle_params']:
            del info['bundle_params']['debug']
        return info
