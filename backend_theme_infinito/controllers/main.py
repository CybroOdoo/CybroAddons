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
#
#############################################################################
import json
import os
import re

from odoo import http
from odoo.http import request


def minify_css(path):
    """Minify css string"""
    with open(path, 'r') as f:
        css = f.read()
    css = re.sub(r'/\*[\s\S]*?\*/', "", css)
    css = re.sub(r'url\((["\'])([^)]*)\1\)', r'url(\2)', css)
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'#([0-9a-f])\1([0-9a-f])\2([0-9a-f])\3(\s|;)', r'#\1\2\3\4',
                 css)
    css = re.sub(r':\s*0(\.\d+([cm]m|e[mx]|in|p[ctx]))\s*;', r':\1;', css)
    rules = re.findall(r'([^{]+){([^}]*)}', css)
    selectors_list = []
    css_values = {}
    for rule in rules:
        selector = rule[0]
        content = rule[1]
        if selector not in selectors_list:
            selectors_list.append(selector)
            css_values[selector] = content
        else:
            css_values[selector] = css_values[selector] + content
    with open(path, 'w') as f:
        selector_dict = {}
        for selector in selectors_list:
            rule = css_values[selector].split(';')
            dict_rule = {}
            for r in rule:
                if r:
                    split_rule = r.split(':')
                    if len(split_rule) == 2:
                        dict_rule[split_rule[0].strip()] = split_rule[1]
            selector_dict[selector] = dict_rule
        f.write('/* This Styles are generated automatically by Theme Studio'
                ' */\n')
        for selector in selector_dict:
            f.write(selector + '{')
            for rule_data in selector_dict[selector]:
                if rule_data != 'pointer-events':
                    if selector_dict[selector][rule_data].find(
                            '!important') == -1:
                        f.write(rule_data + ':' +
                                selector_dict[selector][rule_data] +
                                ' !important;')
                    else:
                        f.write(rule_data + ':' +
                                selector_dict[selector][rule_data] + ';')
            f.write('}')


class ThemeStudio(http.Controller):

    @http.route(['/theme_studio/save_styles'], type="json")
    def save_styles(self, changed_styles, object_class, hover=False):
        """Create Dynamic Styles css file"""
        changed_styles = json.loads(changed_styles)
        working_dir = os.path.dirname(os.path.realpath(__file__))
        working_dir = working_dir.replace('/controllers', '')
        file_path = working_dir + '/static/src/css/dynamic_styles.css'
        style_file = open(file_path, 'a')
        if os.stat(file_path).st_size == 0:
            style_file.write('/* This file is generated automatically by '
                             'Theme Infinito */\n')

        style_file.write('\n.' + object_class + ':hover {\n') if hover else \
            style_file.write('\n.' + object_class + ' {\n')
        for style in changed_styles:
            style_file.write(
                '\t' + style + ': ' + changed_styles[style] + ';\n')
        style_file.write('}\n')
        style_file.close()
        minify_css(file_path)
        return True

    @http.route(['/theme_studio/get_current_style'], type="json")
    def get_current_style(self, selector):
        working_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = working_dir.replace('controllers',
                                        'static/src/css/dynamic_styles.css')
        style_file = open(file_path, 'r')
        css = style_file.read()
        css = re.sub(r'/\*[\s\S]*?\*/', "", css)
        css = re.sub(r'url\((["\'])([^)]*)\1\)', r'url(\2)', css)
        css = re.sub(r'\s+', ' ', css)
        css = re.sub(r'#([0-9a-f])\1([\da-f])\2([0-9a-f])\3(\s|;)',
                     r'#\1\2\3\4', css)
        css = re.sub(r':\s*0(\.\d+([cm]m|e[mx]|in|p[ctx]))\s*;', r':\1;', css)
        rules = re.findall(r'([^{]+){([^}]*)}', css)
        for rule in rules:
            selector_now = rule[0]
            content = rule[1]
            if selector == selector_now.strip():
                contents = content.split(';')
                content = []
                for c in contents:
                    c = c.split(':')
                    if c[0] != '' and len(c) > 1:
                        content.append([c[0], c[1].strip().replace('!important', '')])
                return content

        return False

    @http.route(['/theme_studio/reset_to_default'], type="json")
    def reset_to_default(self):
        working_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = working_dir.replace('controllers',
                                        'static/src/css/dynamic_styles.css')
        style_file = open(file_path, 'w')
        style_file.write('')
        return True

    @http.route(['/theme_studio/set_advanced_data'], type="json")
    def set_advanced_data(self, vals):
        set_param = request.env['ir.config_parameter'].sudo().set_param
        set_param('backend_theme_infinito.is_user_edit', vals['userEdit'])
        set_param('backend_theme_infinito.is_sidebar_enabled', vals['sidebar'])
        set_param('backend_theme_infinito.is_fullscreen_enabled', vals['fullscreen'])
        set_param('backend_theme_infinito.is_sidebar_icon', vals['sidebarIcon'])
        set_param('backend_theme_infinito.is_sidebar_name', vals['sidebarName'])
        set_param('backend_theme_infinito.is_sidebar_company', vals['sidebarCompany'])
        set_param('backend_theme_infinito.is_sidebar_user', vals['sidebarUser'])
        set_param('backend_theme_infinito.is_recent_apps', vals['recentApps'])
        set_param('backend_theme_infinito.is_fullscreen_app', vals['fullScreenApp'])
        set_param('backend_theme_infinito.is_rtl', vals['infinitoRtl'])
        set_param('backend_theme_infinito.is_dark', vals['infinitoDark'])
        set_param('backend_theme_infinito.dark_mode', vals['infinitoDarkMode'])
        set_param('backend_theme_infinito.dark_start', vals['infinitoDarkStart'])
        set_param('backend_theme_infinito.dark_end', vals['infinitoDarkEnd'])
        set_param('backend_theme_infinito.is_menu_bookmark', vals['infinitoBookmark'])
        set_param('backend_theme_infinito.is_chameleon', vals['infinitoChameleon'])

    @http.route(['/theme_studio/set_advanced_data_user'], type="json")
    def set_advanced_data_user(self, vals):
        request.env.user.write({
            'is_sidebar_enabled': vals['sidebar'],
            'is_fullscreen_enabled': vals['fullscreen'],
            'is_sidebar_icon': vals['sidebarIcon'],
            'is_sidebar_name': vals['sidebarName'],
            'is_sidebar_company': vals['sidebarCompany'],
            'is_sidebar_user': vals['sidebarUser'],
            'is_recent_apps': vals['recentApps'],
            'is_fullscreen_app': vals['fullScreenApp'],
            'is_rtl': vals['infinitoRtl'],
            'is_dark': vals['infinitoDark'],
            'dark_mode': vals['infinitoDarkMode'],
            'dark_start': vals['infinitoDarkStart'],
            'dark_end': vals['infinitoDarkEnd'],
            'is_menu_bookmark': vals['infinitoBookmark'],
            'loader_class': vals['loaderClass'],
            'is_chameleon': vals['infinitoChameleon'],
        })

        return True

    @http.route(['/theme_studio/add_recent_app'], type="json")
    def add_recent_app(self, app):
        recent_app = request.env['recent.apps'].sudo()
        exist = recent_app.search([
            ('app_id', '=', int(app.get('appId'))),
            ('user_id', '=', request.env.user.id)
        ])
        exist.unlink() if exist else None
        total_recent = recent_app.search([('user_id', '=', request.env.user.id)])
        if len(total_recent) > 4:
            total_recent[0].unlink()
        recent_app.create({
            'app_id': int(app.get('appId')),
            'user_id': request.env.user.id
        })

    @http.route(['/theme_studio/get_recent_apps'], type="json")
    def get_recent_apps(self):
        recent_app = request.env['recent.apps'].sudo()
        return recent_app.search_read([
            ('user_id', '=', request.env.user.id)
        ])

    @http.route(['/theme_studio/add_menu_bookmarks'], type="json")
    def add_menu_bookmarks(self, menu):
        menu_bookmark = request.env['infinito.menu.bookmark'].sudo()
        menu_bookmark.create({
            'action_id': int(menu.get('actionId')),
            'user_id': request.env.user.id,
            'url': menu.get('menuUrl'),
        })

    @http.route(['/theme_studio/remove_menu_bookmarks'], type="json")
    def remove_menu_bookmarks(self, menu):
        menu_bookmark = request.env['infinito.menu.bookmark'].sudo().search([
            ('action_id', '=', int(menu.get('actionId'))),
            ('user_id', '=', request.env.user.id)
        ])
        if menu_bookmark:
            menu_bookmark.unlink()

    @http.route(['/theme_studio/get_presets'], type="json")
    def get_presets(self):
        working_dir = os.path.dirname(os.path.realpath(__file__))
        working_dir = working_dir.replace('/controllers', '')
        file_path = working_dir + '/static/src/json/presets.json'
        file = open(file_path, 'r')
        presets = json.load(file)

        return presets
