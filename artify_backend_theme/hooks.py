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
import base64
from odoo import tools


def process_menu_item(menu):
    """
       Process a menu item by updating its web_icon_data.
       param:
           menu (record): The menu item to process.
       """
    menu_list = [
        'Contacts', 'Link Tracker', 'Dashboards', 'Sales', 'Invoicing',
        'Inventory', 'Purchase', 'Calendar', 'Point of Sale', 'Website',
        'Notes', 'CRM', 'Surveys', 'Project', 'SMS Marketing',
        'Email Marketing', 'Repairs', 'Manufacturing', 'Timesheets',
        'Fleet', 'Lunch', 'Live Chat', 'Maintenance', 'Expenses', 'Time Off',
        'Attendances', 'Recruitment', 'Employees', 'Members', 'eLearning',
        'Events'
    ]
    if menu.name not in menu_list:
        return
    img_path = tools.misc.file_path(
        f'artify_backend_theme/static/src/img/icons/{menu.name}.png')
    with open(img_path, "rb") as img_file:
        menu.write({'web_icon_data': base64.b64encode(img_file.read())})


def init_hooks(env):
    """
        Initialize hooks by updating the web_icon_data of certain menus.
        param:
            env (Environment): Odoo environment.
        """
    menu_item = env['ir.ui.menu'].search([('parent_id', '=', False)])
    for menu in menu_item:
        process_menu_item(menu)
