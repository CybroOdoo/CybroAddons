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
from odoo.addons.backend_theme_infinito.models.ir_http import to_bool

NO_FONT_VALUES = (False, None, '', '0', 'False', 'false')


def get_current_lang(languages, lang_code):
    """Return the (code, name) pair of ``lang_code`` or the first language."""
    for lang in languages:
        if lang[0] == lang_code:
            return lang
    return languages[0] if languages else ['', '']


class IrHttp(models.AbstractModel):
    """Adds the Infinito Plus values to the session information."""
    _inherit = 'ir.http'

    def session_info(self):
        res = super().session_info()
        languages = self.env['res.lang'].get_installed()
        res['currentLang'] = get_current_lang(languages, self.env.user.lang)
        res['availableLanguages'] = languages
        if self.env.user.has_group('base.group_user'):
            get_param = self.env['ir.config_parameter'].sudo().get_param
            user = self.env.user
            user_edit = to_bool(get_param('backend_theme_infinito.is_user_edit'))
            if user_edit and not user.has_group('base.group_system'):
                res['infinitoRefresh'] = user.is_refresh
            else:
                res['infinitoRefresh'] = to_bool(
                    get_param('backend_theme_infinito_plus.is_refresh'))
            res['chatBoxPosition'] = get_param(
                'backend_theme_infinito_plus.chatterbox_position', default=False)
            res['infinitoAnimation'] = get_param(
                'backend_theme_infinito_plus.animation_plus', default=False)
            font_id = get_param('backend_theme_infinito_plus.font', default=False)
            res['infinitoGoogleFont'] = False if font_id in NO_FONT_VALUES else font_id
        return res