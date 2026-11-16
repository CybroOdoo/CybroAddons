# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################


def apply_velora_theme(env):
    """Copy theme_velora's views, pages and menus onto the first website.

    This is what 'Use this theme' does, minus the module install/upgrade step,
    which Odoo forbids inside tests. Returns the website.
    """
    website = env['website'].search([], limit=1)
    module = env['ir.module.module'].search([('name', '=', 'theme_velora')])
    website.theme_id = module
    module.with_context(website_id=website.id)._theme_load(website)
    return website