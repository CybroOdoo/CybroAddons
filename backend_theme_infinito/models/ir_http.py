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
from odoo import models


def float_to_time(time):
    """
    Convert a floating-point number representing time in hours to a string
    formatted as 'HH:MM'.

    Parameters:
    - time (float): The time in hours to be converted.

    Returns:
    - str: A string representing the time in the format 'HH:MM'.
   """
    return '{0:02.0f}:{1:02.0f}'.format(*divmod(float(time) * 60, 60))


class IrHttp(models.AbstractModel):
    """
    Extends the 'ir.http' model to customize session information for the
    web client.
    """
    _inherit = 'ir.http'

    def session_info(self):
        """
           Overrides the default session_info method to customize session
           information based on user preferences.

           Returns:
           - dict: A dictionary containing session information customized for
           the current user.
       """
        res = super(IrHttp, self).session_info()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        if self.env.user.has_group('base.group_user'):
            user_edit = get_param(
                'backend_theme_infinito.is_user_edit', default=False)
            res['userEdit'] = user_edit
            if user_edit:
                res['sidebar'] = self.env.user.is_sidebar_enabled
                res['fullscreen'] = self.env.user.is_fullscreen_enabled
                res['sidebarIcon'] = self.env.user.is_sidebar_icon
                res['sidebarName'] = self.env.user.is_sidebar_name
                res['sidebarCompany'] = self.env.user.is_sidebar_company
                res['sidebarUser'] = self.env.user.is_sidebar_user
                res['recentApps'] = self.env.user.is_recent_apps
                res['fullScreenApp'] = self.env.user.is_fullscreen_app
                res['infinitoRtl'] = self.env.user.is_rtl
                res['infinitoDark'] = self.env.user.is_dark
                res['infinitoDarkMode'] = self.env.user.dark_mode
                res['infinitoDarkStart'] = float_to_time(
                    self.env.user.dark_start)
                res['infinitoDarkEnd'] = float_to_time(self.env.user.dark_end)
                res['infinitoBookmark'] = self.env.user.is_menu_bookmark
                res['loaderClass'] = self.env.user.loader_class
            else:
                res['sidebar'] = get_param(
                    'backend_theme_infinito.is_sidebar_enabled', default=False)
                res['fullscreen'] = get_param(
                    'backend_theme_infinito.is_fullscreen_enabled',
                    default=False)
                res['sidebarIcon'] = get_param(
                    'backend_theme_infinito.is_sidebar_icon', default=False)
                res['sidebarName'] = get_param(
                    'backend_theme_infinito.is_sidebar_name', default=False)
                res['sidebarCompany'] = get_param(
                    'backend_theme_infinito.is_sidebar_company', default=False)
                res['sidebarUser'] = get_param(
                    'backend_theme_infinito.is_sidebar_user', default=False)
                res['recentApps'] = get_param(
                    'backend_theme_infinito.is_recent_apps', default=False)
                res['fullScreenApp'] = get_param(
                    'backend_theme_infinito.is_fullscreen_app', default=False)
                res['infinitoRtl'] = get_param(
                    'backend_theme_infinito.is_rtl', default=False)
                res['infinitoDark'] = get_param(
                    'backend_theme_infinito.is_dark', default=False)
                res['infinitoDarkMode'] = get_param(
                    'backend_theme_infinito.dark_mode', default=False)
                res['infinitoDarkStart'] = float_to_time(get_param(
                    'backend_theme_infinito.dark_start', default=19.0))
                res['infinitoDarkEnd'] = float_to_time(get_param(
                    'backend_theme_infinito.dark_end', default=5.0))
                res['infinitoBookmark'] = get_param(
                    'backend_theme_infinito.is_menu_bookmark', default=False)
                res['loaderClass'] = get_param(
                    'backend_theme_infinito.loader_class', default=False)
            menu_bookmark = self.env['infinito.menu.bookmark'].sudo(). \
                search([('user_id', '=', self.env.user.id)])
            list_bookmark = []
            for bookmark in menu_bookmark:
                bkm = bookmark.read(['action_id', 'url', 'name'])[0]
                bkm['short_name'] = bkm['name'][:2].upper()
                list_bookmark.append(bkm)
            res['infinitoBookmarks'] = menu_bookmark.action_id.ids
            res['infinitoMenuBookmarks'] = list_bookmark

        return res
