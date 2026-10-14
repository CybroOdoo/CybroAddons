# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from . import models
from . import controllers

def post_init_hook(env):
    website = env['website'].get_current_website()
    theme = env['ir.module.module'].search([('name', '=', 'theme_cineverse')], limit=1)
    if website and theme:
        website.theme_id = theme.id


def uninstall_hook(env):
    cineverse_theme_menus = env['theme.website.menu'].search([])
    menus = env['website.menu'].search([
        ('theme_template_id', 'in', cineverse_theme_menus.ids)
    ])
    menus.unlink()
