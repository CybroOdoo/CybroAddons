# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sigha CK (odoo@cybrosys.com)
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
from odoo import models


class IrHttp(models.AbstractModel):
    """Class for session information"""
    _inherit = 'ir.http'

    def session_info(self):
        """pass the session information """
        res = super(IrHttp, self).session_info()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        all_langs = self.env['res.lang'].get_installed()
        res['currentLang'] = \
            list(filter(lambda x: x[0] == self.env.user.lang, all_langs))[0]
        res['availableLanguages'] = all_langs
        if self.env.user.has_group('base.group_user'):
            user_edit = get_param(
                'backend_theme_infinito_plus.is_user_edit', default=False)
            res['userEdit'] = user_edit
            if user_edit:
                res['infinitoRefresh'] = self.env.user.is_refresh
            else:
                res['infinitoRefresh'] = get_param(
                    'backend_theme_infinito_plus.is_refresh', default=False)
                res['chatBoxPosition'] = get_param(
                    'backend_theme_infinito_plus.chatbox_position',
                    default=False)
                res['infinitoAnimation'] = get_param(
                    'backend_theme_infinito_plus.animation_plus',
                    default=False)
        return res
