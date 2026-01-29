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
from odoo import fields, models


class User(models.Model):
    _inherit = 'res.users'

    is_sidebar_enabled = fields.Boolean('Sidebar Enabled', default=False)
    is_fullscreen_enabled = fields.Boolean('Full screen Enabled', default=False)
    is_sidebar_icon = fields.Boolean('Sidebar icon Enabled', default=True)
    is_sidebar_name = fields.Boolean('Sidebar name Enabled', default=True)
    is_sidebar_company = fields.Boolean('Sidebar Company Enabled',
                                        default=False)
    is_sidebar_user = fields.Boolean('Sidebar User Enabled', default=False)
    is_recent_apps = fields.Boolean('Recent Apps Enabled', default=False)
    is_fullscreen_app = fields.Boolean('Full screen Apps Enabled',
                                       default=False)
    is_rtl = fields.Boolean('Rtl Enabled', default=False)
    is_dark = fields.Boolean('Dark mode Enabled', default=False)
    is_menu_bookmark = fields.Boolean('Menu Bookmark mode Enabled',
                                      default=False)
    is_chameleon = fields.Boolean('Chameleon mode Enabled', default=False)
    dark_mode = fields.Selection([
        ('all', 'All'),
        ('schedule', 'Schedule'),
        ('auto', 'Automatic'),
    ], default='all')
    dark_start = fields.Float('Dark Start', default=19.0)
    dark_end = fields.Float('Dark End', default=5.0)
    loader_class = fields.Char('Loader', default='default')
