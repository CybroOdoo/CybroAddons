# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#
#############################################################################
import json
import os

from odoo import http
from odoo.http import request
from odoo.addons.backend_theme_infinito.controllers.main import ThemeStudio
from odoo.addons.backend_theme_infinito.controllers.main import minify_css


class ThemeStudioPlus(ThemeStudio):
    """Controller for updating the changes from infinito control panel"""

    @http.route(['/theme_studio/save_styles_plus'], type="json")
    def save_styles_plus(self, new_style):
        """Create Dynamic Styles css file for chat box layout"""
        changed_styles = json.loads(new_style)
        working_dir = os.path.dirname(os.path.realpath(__file__))
        working_dir = working_dir.replace('/controllers', '')
        file_path = working_dir + '/static/src/css/chatter.css'
        style_file = open(file_path, 'a')
        style_file.truncate(0)
        if os.stat(file_path).st_size == 0:
            style_file.write('/* This file is generated automatically by '
                             'Theme Infinito Plus */\n')
            style_file.write('.o_ChatWindow' + ' {\n')
            for i in changed_styles[0]:
                style_file.write('\t' + i + ':' + changed_styles[0][i] + ';\n')
            style_file.write('}\n')
            style_file.close()
            minify_css(file_path)
        return True

    @http.route(['/theme_studio/animation_styles'], type="json")
    def animation_styles(self, style):
        """ create the Dynamic css file for animation"""
        animated = json.loads(style)
        saved_style = animated[0]
        working_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = working_dir.replace('/controllers',
                                        '/static/src/scss/animation.scss')
        read_file = open(file_path, 'r')
        css = read_file.read()
        write_file = open(file_path, 'w')
        for line in css.split('\n'):
            if 'ease-in' in line:
                write_file.write(css.replace(line.strip(),
                                             'animation:' + saved_style + ' #{$tr * .1}s ease-in !important;'))
        write_file.close()
        read_file.close()

    @http.route(['/theme_studio/font_style'], type="json")
    def font_style(self, font_id):
        """updating th e google fonts"""
        font_obj = request.env['infinito.google.font']
        if font_id == 0:
            font_obj.remove_fonts()
        else:
            font_obj.browse(font_id).set_css()

    @http.route(['/theme_studio/set_advanced_plus_data'], type="json")
    def set_advanced_data_plus(self, vals):
        """ save the features from theme studio"""
        set_param = request.env['ir.config_parameter'].sudo().set_param
        set_param('backend_theme_infinito_plus.is_refresh',
                  vals['infinitoRefresh'])
        set_param('backend_theme_infinito_plus.chatbox_position',
                  vals['chatBoxPosition'])
        set_param('backend_theme_infinito_plus.google_font',
                  vals['infinitoGoogleFont'])
        if 'infinitoAnimation' in vals.keys():
            set_param('backend_theme_infinito_plus.animation_plus',
                      vals['infinitoAnimation'])

    @http.route(['/theme_studio/set_advanced_plus_data_user'], type="json")
    def set_advanced_plus_data_user(self, vals):
        """"updating the user inifnito data"""
        request.env.user.write({
            'is_refresh': vals['infinitoRefresh'],
            'chatbox_position': vals['chatBoxPosition'],
            'animation_plus': vals['infinitoAnimation']
        })
        return True

    @http.route(['/theme_studio_plus/reset_to_default_style'], type="json")
    def reset_to_default_style(self):
        """rest to default styles"""
        working_dir = os.path.dirname(os.path.realpath(__file__))
        style_file_path = working_dir.replace('controllers',
                                              'static/src/css/font.css')
        animation_file_path = working_dir.replace('controllers',
                                                  'static/src/scss/animation.scss')
        chat_file_path = working_dir.replace('controllers',
                                             'static/src/css/chatter.css')
        style_file = open(style_file_path, 'w')
        style_file.write('')
        animation_read_file = open(animation_file_path, 'r')
        animation_css = animation_read_file.read()
        animation_file = open(animation_file_path, 'w')
        for line in animation_css.split('\n'):
            if 'ease-in' in line:
                animation_file.write(animation_css.replace(line.strip(),
                                                           'animation:' + 'infinito_kanban_shake' + ' #{$tr * .1}s ease-in !important;'))
        chat_file = open(chat_file_path, 'w')
        chat_file.write('')
        request.env['ir.config_parameter'].sudo().set_param(
            'backend_theme_infinito_plus.is_refresh', False)
        return True
