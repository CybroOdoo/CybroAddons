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
from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from ..models.utils import get_param, set_param, to_bool

CHATBOX_POSITIONS = {
    'Top Right': {'top': '10px', 'right': '10px', 'bottom': 'auto', 'left': 'auto'},
    'Top Left': {'top': '10px', 'left': '10px', 'bottom': 'auto', 'right': 'auto'},
    'Bottom Left': {'bottom': '10px', 'left': '10px', 'top': 'auto', 'right': 'auto'},
    'Bottom Right': {'bottom': '10px', 'right': '10px', 'top': 'auto', 'left': 'auto'},
}
ANIMATIONS = ('Default', 'Scale', 'Slide in')


class ThemeStudioPlus(http.Controller):
    """Routes behind the Infinito Plus options of Theme Studio."""

    @staticmethod
    def _check_admin():
        if not request.env.user.has_group('base.group_system'):
            raise AccessError(
                request.env._('Only administrators can change the theme.'))

    def _save_user_options(self, vals):
        """Save the options a normal user may change for themselves."""
        user_edit = to_bool(get_param(
            request.env, 'backend_theme_infinito.is_user_edit'))
        if not user_edit or not request.env.user.has_group('base.group_user'):
            raise AccessError(
                request.env._('Users cannot edit these settings.'))
        request.env.user.sudo().write(
            {'is_refresh': bool(vals.get('infinitoRefresh'))})
        return 'user'

    def _save_global_options(self, vals):
        """Save the options shared by every user (administrators only)."""
        env = request.env
        position = vals.get('chatBoxPosition')
        animation = vals.get('infinitoAnimation')
        try:
            font_id = int(vals.get('infinitoGoogleFont') or 0)
        except (TypeError, ValueError):
            font_id = 0
        if font_id and not env['infinito.google.font'].browse(font_id).exists():
            font_id = 0
        refresh = bool(vals.get('infinitoRefresh'))
        set_param(env, 'backend_theme_infinito_plus.is_refresh', refresh)
        set_param(env, 'backend_theme_infinito_plus.chatterbox_position',
                  position if position in CHATBOX_POSITIONS else False)
        set_param(env, 'backend_theme_infinito_plus.animation_plus',
                  animation if animation in ANIMATIONS else False)
        set_param(env, 'backend_theme_infinito_plus.font', font_id)
        # Keep the admin's own flag in step, so turning Refresh off works
        env.user.sudo().write({'is_refresh': refresh})
        return 'global'

    @http.route(['/theme_studio/set_advanced_data_plus'],
                type="jsonrpc", auth="user")
    def set_advanced_data_plus(self, args):
        """Save the Infinito Plus options for the current user.

        Administrators save the global options. Other users can only save
        their own refresh option, and only when "User edit" is enabled.
        """
        if not (args and isinstance(args[0], dict) and 'vals' in args[0]):
            return False
        vals = args[0]['vals']
        if request.env.user.has_group('base.group_system'):
            return self._save_global_options(vals)
        return self._save_user_options(vals)

    @http.route(['/theme_studio_plus/set_user_lang'],
                type="jsonrpc", auth="user")
    def set_user_lang(self, lang):
        """Change the language of the current user."""
        if lang not in dict(request.env['res.lang'].get_installed()):
            raise UserError(request.env._('This language is not installed.'))
        request.env.user.write({'lang': lang})
        return True

    @http.route(['/theme_studio_plus/reset_to_default_style'],
                type="jsonrpc", auth="user")
    def reset_to_default_style(self):
        """Remove the font, chatbox and animation settings."""
        self._check_admin()
        for key in ('font', 'chatterbox_position', 'animation_plus'):
            set_param(request.env, 'backend_theme_infinito_plus.%s' % key, False)
        return True

    @http.route('/backend_theme_infinito_plus/dynamic_styles.css',
                type='http', auth='public')
    def dynamic_styles(self):
        """Serve the font and chatbox CSS built from the saved options."""
        env = request.env
        rules = [env['infinito.google.font'].sudo().get_active_font_css()]
        position = CHATBOX_POSITIONS.get(get_param(
            env, 'backend_theme_infinito_plus.chatterbox_position'))
        if position:
            declarations = ''.join(
                '%s:%s!important;' % item for item in position.items())
            rules.append('.o-mail-ChatWindow{%s}' % declarations)
        return request.make_response('\n'.join(r for r in rules if r), headers=[
            ('Content-Type', 'text/css; charset=utf-8'),
            ('Cache-Control', 'no-cache, no-store, must-revalidate'),
        ])