# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models


class IrHttp(models.AbstractModel):
    """Model for session information.

    This abstract model is used for handling session information.

    Attributes:
        _inherit (str): Name of the model to inherit from.

    """
    _inherit = 'ir.http'

    def session_info(self):
        """Pass the session information.

        This method extends the functionality of retrieving session information
        by adding additional data such as the current language, available languages,
        user edit permissions, refresh status, chat box position, and animation settings.

        Returns:
            dict: A dictionary containing session information.

        """
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
            if self.env.user.is_refresh:
                res['infinitoRefresh'] = self.env.user.is_refresh
            else:
                res['infinitoRefresh'] = get_param(
                    'backend_theme_infinito_plus.is_refresh', default=False)
            res['chatBoxPosition'] = get_param(
                'backend_theme_infinito_plus.chatterbox_position',
                default=False)
            res['infinitoAnimation'] = get_param(
                'backend_theme_infinito_plus.animation_plus',
                default=False)
            res['infinitoGoogleFont'] = get_param(
                'backend_theme_infinito_plus.font',
                default=False)
        return res
