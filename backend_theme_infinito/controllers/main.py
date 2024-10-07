# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    """
    Minify CSS file located at the specified path.

    Parameters:
        path (str): The file path to the CSS file to be minified.

    Returns:
        None

    This function reads the CSS file specified by the given path, removes
    comments,excess whitespace, and redundant CSS properties. It then writes
    the minified CSS back to the same file, overwriting its previous contents.

    Note:
        This function modifies the CSS file in place.

    Example:
        minify_css('/path/to/style.css')
    """
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
    """
    Controller class for managing themes in a web application.

    This controller handles requests related to managing themes, such as
    applying themes, customizing themes, and saving theme settings.
    """

    @http.route(['/theme_studio/save_styles'], type="json")
    def save_styles(self, kwargs):
        """
        Save dynamic styles to a CSS file.

        Parameters:
            kwargs (dict): A dictionary containing the changed_styles and
            object_class.

        Returns:
            bool: True if the styles are successfully saved, otherwise False.

        This function takes the changed_styles and object_class from the
        kwargs dictionary and saves them to a CSS file. It appends the styles
        to an existing file or creates a new file if it doesn't exist.
        After saving the styles, it minifies the CSS file.

        Example:
            To save styles for a specific object class:

            ```python
            from my_theme_module import save_styles

            save_styles({
                'changed_styles': {
                    'color': 'red',
                    'font-size': '16px'
                },
                'object_class': 'my-object'
            })
            ```
        """
        changed_styles_str = kwargs.get('changed_styles', '{}')
        object_class = kwargs.get('object_class', '')
        changed_styles = json.loads(changed_styles_str)
        working_dir = os.path.dirname(os.path.realpath(__file__))
        working_dir = working_dir.replace('/controllers', '')
        file_path = working_dir + '/static/src/css/dynamic_styles.css'
        style_file = open(file_path, 'a')

        if os.stat(file_path).st_size == 0:
            style_file.write('/* This file is generated automatically by '
                             'Theme Infinito */\n')

        style_file.write('\n.' + object_class + ' {\n')

        for style in changed_styles:
            style_file.write(
                '\t' + style + ': ' + changed_styles[style] + ';\n')

        style_file.write('}\n')
        style_file.close()
        minify_css(file_path)
        return True

    @http.route(['/theme_studio/get_current_style'], type="json")
    def get_current_style(self, kwargs):
        """
       Retrieve the current styles for a given CSS selector.

       Parameters:
           kwargs (dict): A dictionary containing the 'selector' key
           specifying the CSS selector.

       Returns:
           list or bool: A list of style properties and values for the
           specified selector, or False if the selector is not found.

       This function reads the CSS file containing dynamic styles and
       searches for the specified CSS selector. If the selector is found,
       it returns a list of style properties and values associated with that
       selector. Each style property-value pair is represented as a list
       containing the property and its corresponding value.
       If the selector is not found,it returns False.

       Example:
           To retrieve the current styles for a specific CSS selector:

           ```python
           from my_theme_module import get_current_style

           current_styles = get_current_style({
               'selector': '.my-selector'
           })
           print(current_styles)
           # Output: [['color', 'red'], ['font-size', '16px']]
           ```
       """
        selector = kwargs.get('selector', '')
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
                        content.append(
                            [c[0], c[1].strip().replace('!important', '')])
                return content

        return False

    @http.route(['/theme_studio/reset_to_default'], type="json")
    def reset_to_default(self):
        """
        Reset dynamic styles to default.

        Returns:
            bool: True if the styles are successfully reset, otherwise False.

        This function clears the content of the CSS file containing
        dynamic styles, effectively resetting all styles to their default
        values.

        Example:
            To reset dynamic styles to default:

            ```python
            from my_theme_module import reset_to_default

            reset_to_default()
            ```
        """
        working_dir = os.path.dirname(os.path.realpath(__file__))
        file_path = working_dir.replace('controllers',
                                        'static/src/css/dynamic_styles.css')
        style_file = open(file_path, 'w')
        style_file.write('')
        return True

    @http.route(['/theme_studio/set_advanced_data'], type="json")
    def set_advanced_data(self, args):
        """
        Set advanced theme configuration data.

        Parameters:
            args (list): A list containing a dictionary with the advanced
            theme configuration values.

        Returns:
            bool: True if the configuration data is successfully set,
            otherwise False.

        This function sets advanced theme configuration data based on the
        provided dictionary of values. It updates the configuration
        parameters in the database accordingly.

        Example:
            To set advanced theme configuration data:

            ```python
            from my_theme_module import set_advanced_data

            data = [{
                'vals': {
                    'sidebar': True,
                    'fullscreen': False,
                    'sidebarIcon': True,
                    'sidebarName': True,
                    'sidebarCompany': False,
                    'sidebarUser': True,
                    'recentApps': False,
                    'fullScreenApp': True,
                    'infinitoRtl': False,
                    'infinitoDark': True,
                    'infinitoDarkMode': 'dark',
                    'infinitoBookmark': True
                }
            }]

            set_advanced_data(data)
            ```
        """
        if args and 'vals' in args[0]:
            vals = args[0]['vals']
            set_param = request.env['ir.config_parameter'].sudo().set_param
            set_param('backend_theme_infinito.is_sidebar_enabled',
                      vals['sidebar'])
            set_param('backend_theme_infinito.is_fullscreen_enabled',
                      vals['fullscreen'])
            set_param('backend_theme_infinito.is_sidebar_icon',
                      vals['sidebarIcon'])
            set_param('backend_theme_infinito.is_sidebar_name',
                      vals['sidebarName'])
            set_param('backend_theme_infinito.is_sidebar_company',
                      vals['sidebarCompany'])
            set_param('backend_theme_infinito.is_sidebar_user',
                      vals['sidebarUser'])
            set_param('backend_theme_infinito.is_recent_apps',
                      vals['recentApps'])
            set_param('backend_theme_infinito.is_fullscreen_app',
                      vals['fullScreenApp'])
            set_param('backend_theme_infinito.is_rtl', vals['infinitoRtl'])
            set_param('backend_theme_infinito.is_dark', vals['infinitoDark'])
            set_param('backend_theme_infinito.dark_mode',
                      vals['infinitoDarkMode'])
            set_param('backend_theme_infinito.is_menu_bookmark',
                      vals['infinitoBookmark'])

    @http.route(['/theme_studio/set_advanced_data_user'], type="json")
    def set_advanced_data_user(self, args):
        """
        Set advanced theme configuration data for the current user.

        Parameters:
            args (list): A list containing a dictionary with the advanced
            theme configuration values.

        Returns:
            bool: True if the configuration data is successfully set for the
            user, otherwise False.

        This function sets advanced theme configuration data for the current
        user based on the provided dictionary of values. It updates the
        corresponding fields in the user record accordingly.

        Example:
            To set advanced theme configuration data for the current user:

            ```python
            from my_theme_module import set_advanced_data_user

            data = [{
                'vals': {
                    'sidebar': True,
                    'fullscreen': False,
                    'sidebarIcon': True,
                    'sidebarName': True,
                    'sidebarCompany': False,
                    'sidebarUser': True,
                    'recentApps': False,
                    'fullScreenApp': True,
                    'infinitoRtl': False,
                    'infinitoDark': True,
                    'infinitoDarkMode': 'dark',
                    'infinitoBookmark': True,
                    'loaderClass': 'custom-loader'
                }
            }]

            set_advanced_data_user(data)
            ```
        """
        if args and 'vals' in args[0]:
            vals = args[0]['vals']
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
                'is_menu_bookmark': vals['infinitoBookmark'],
                'loader_class': vals['loaderClass']
            })

            return True

    @http.route(['/theme_studio/add_recent_app'], type="json")
    def add_recent_app(self, args):
        """
        Add a recent application to the user's recent apps list.

        Parameters:
            args (list): A list containing a dictionary with the 'appId' key
            specifying the ID of the application.

        Returns:
            bool: True if the recent app is successfully added, otherwise False.

        This function adds a recent application to the user's recent apps list
        based on the provided application ID. It checks if the provided
        arguments are valid and if the user has already reached the maximum
        limit of recent apps (5), it removes the oldest one before adding the
        new one.

        Example:
            To add a recent application with ID 123 to the user's recent apps
            list:

            ```python
            from my_theme_module import add_recent_app

            add_recent_app([{'appId': 123}])
            ```
        """
        if args and isinstance(args, list) and len(args) > 0:
            app_id = args[0].get('appId')
            if app_id is not None:  # Check if appId exists
                app_id = int(app_id)
            else:
                # Handle the case where appId is not provided
                # You might want to raise an error, log a message, or handle
                # it differently based on your requirements
                # For now, I'll assign a default value of 0
                app_id = 0
        else:
            # Handle the case where args is empty or not a list
            # You might want to raise an error or handle it differently based
            # on your requirements For now, I'll assign a default value of 0
            app_id = 0

        recent_app = request.env['recent.apps'].sudo()
        exist = recent_app.search([
            ('app_id', '=', app_id),
            ('user_id', '=', request.env.user.id)
        ])
        exist.unlink() if exist else None
        total_recent = recent_app.search(
            [('user_id', '=', request.env.user.id)])
        if len(total_recent) > 4:
            total_recent[0].unlink()
        recent_app.create({
            'app_id': app_id,
            'user_id': request.env.user.id
        })

    @http.route(['/theme_studio/get_recent_apps'], type="json")
    def get_recent_apps(self):
        """
       Retrieve the list of recent applications for the current user.

       Returns:
           list: A list of dictionaries containing the recent applications'
           information,
               or an empty list if no recent apps are found.

       This function retrieves the list of recent applications for the current
       user from the database. It returns a list of dictionaries containing the
       information of each recent application, such as its ID, name, and other
       relevant details.

       Example:
           To retrieve the list of recent applications for the current user:

           ```python
           from my_theme_module import get_recent_apps

           recent_apps = get_recent_apps()
           print(recent_apps)
           ```
       """
        recent_app = request.env['recent.apps'].sudo()
        return recent_app.search_read([
            ('user_id', '=', request.env.user.id)
        ])

    @http.route(['/theme_studio/add_menu_bookmarks'], type="json")
    def add_menu_bookmarks(self, args):
        """
        Add a menu bookmark for the current user.

        Parameters:
            args (dict): A dictionary containing the menu data including
            'actionId' and 'menuUrl'.

        Returns:
            bool: True if the menu bookmark is successfully added, otherwise
            False.

        This function adds a menu bookmark for the current user based on the
        provided
        menu data. It extracts the action ID and URL from the menu data and
        creates a
        new menu bookmark record in the database.

        Example:
            To add a menu bookmark with action ID 123 and URL '/dashboard' for
            the current user:

            ```python
            from my_theme_module import add_menu_bookmarks

            menu_data = {
                'actionId': 123,
                'menuUrl': '/dashboard'
            }
            add_menu_bookmarks({'menu': menu_data})
            ```
        """
        menu_data = args.get('menu', {})
        action_id = menu_data.get('actionId')
        user_id = request.env.user.id
        url = menu_data.get('menuUrl')
        menu_bookmark = request.env['infinito.menu.bookmark'].sudo()
        menu_bookmark.create({
            'action_id': int((action_id)),
            'user_id': user_id,
            'url': url,
        })

    @http.route(['/theme_studio/remove_menu_bookmarks'], type="json")
    def remove_menu_bookmarks(self, args):
        """
        Remove a menu bookmark for the current user.

        Parameters:
            args (dict): A dictionary containing the menu data including
            'actionId'.

        Returns:
            bool: True if the menu bookmark is successfully removed,
            otherwise False.

        This function removes a menu bookmark for the current user based on
        the provided
        action ID. It searches for the menu bookmark record in the database and
        deletes
        it if found.

        Example:
            To remove a menu bookmark with action ID 123 for the current user:

            ```python
            from my_theme_module import remove_menu_bookmarks

            menu_data = {
                'actionId': 123
            }
            remove_menu_bookmarks({'menu': menu_data})
            ```
        """
        menu_data = args.get('menu', {})
        action_id = menu_data.get('actionId')
        user_id = request.env.user.id
        menu_bookmark = request.env['infinito.menu.bookmark'].sudo().search([
            ('action_id', '=', int(action_id)),
            ('user_id', '=', user_id)
        ])
        if menu_bookmark:
            menu_bookmark.unlink()

    @http.route(['/theme_studio/get_presets'], type="json")
    def get_presets(self):
        """
        Retrieve the list of available presets.

        Returns:
            list: A list of dictionaries containing the available presets.

        This function reads the presets data from a JSON file and returns
        it as a list of dictionaries.
        Each dictionary in the list represents a preset with
        its configuration details.

        Example:
            To retrieve the list of available presets:

            ```python
            from my_theme_module import get_presets

            presets = get_presets()
            print(presets)
            ```
        """
        working_dir = os.path.dirname(os.path.realpath(__file__))
        working_dir = working_dir.replace('/controllers', '')
        file_path = working_dir + '/static/src/json/presets.json'
        file = open(file_path, 'r')
        presets = json.load(file)

        return presets
