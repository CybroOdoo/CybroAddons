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

from .utils import get_param, to_bool


class IrHttp(models.AbstractModel):
    """Add the Infinito Plus options to the session information."""
    _inherit = 'ir.http'

    def session_info(self):
        res = super().session_info()
        user = self.env.user
        all_langs = self.env['res.lang'].get_installed()
        res['currentLang'] = next(
            (lang for lang in all_langs if lang[0] == user.lang),
            all_langs[0] if all_langs else ('', ''))
        res['availableLanguages'] = all_langs
        if user.has_group('base.group_user'):
            # Only set when the base theme did not already provide it
            res.setdefault('userEdit', to_bool(get_param(
                self.env, 'backend_theme_infinito.is_user_edit')))
            res['infinitoRefresh'] = bool(
                user.is_refresh or to_bool(get_param(
                    self.env, 'backend_theme_infinito_plus.is_refresh')))
            res['chatBoxPosition'] = get_param(
                self.env, 'backend_theme_infinito_plus.chatterbox_position')
            res['infinitoAnimation'] = get_param(
                self.env, 'backend_theme_infinito_plus.animation_plus')
            res['infinitoGoogleFont'] = get_param(
                self.env, 'backend_theme_infinito_plus.font')
        return res