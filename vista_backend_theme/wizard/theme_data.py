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
import base64
from odoo import api, fields, models
from odoo.modules import get_module_resource


class ThemeData(models.TransientModel):
    """create a TransientModel for a wizard"""
    _name = "theme.data"

    def _get_current_theme(self):
        """Create a function for get the Current theme"""
        return self.env['theme.data.stored'].sudo().search([], limit=1).name

    name = fields.Selection([
        ('default', 'Default'),
        ('two', 'Green'),
        ('three', 'Black'),
    ], 'Theme', required=True, default=_get_current_theme)

    @api.onchange('name')
    def _onchange_name(self):
        """changing the name using on Change"""
        theme = self.sudo().env.ref('vista_backend_theme.theme_data_stored')
        if theme:
            theme.name = self.name
        else:
            theme.create({
                'name': self.name
            })

    def action_apply(self):
        """create Apply action for the wizard """
        name = self.env['theme.data.stored'].sudo().search([], limit=1).name
        if name == 'two':
            self.env.ref(
                'vista_backend_theme.vista_theme_css_black').active = False
            self.env.ref(
                'vista_backend_theme.vista_theme_css_login_black').active = False
            self.env.ref(
                'vista_backend_theme.vista_theme_css_green').active = True
            self.env.ref(
                'vista_backend_theme.vista_theme_css_login_green').active = True
            self.icon_change_theme_green()
        elif name == 'three':
            self.env.ref(
                'vista_backend_theme.vista_theme_css_green').active = False
            self.env.ref(
                'vista_backend_theme.vista_theme_css_login_green').active = False
            self.env.ref(
                'vista_backend_theme.vista_theme_css_black').active = True
            self.env.ref(
                'vista_backend_theme.vista_theme_css_login_black').active = True
            self.icon_change_theme_default()
        else:
            self.env.ref(
                'vista_backend_theme.vista_theme_css_green').active = False
            self.env.ref(
                'vista_backend_theme.vista_theme_css_black').active = False
            self.env.ref(
                'vista_backend_theme.vista_theme_css_login_green').active = False
            self.env.ref(
                'vista_backend_theme.vista_theme_css_login_black').active = False
            self.icon_change_theme_default()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def icon_change_theme_default(self):
        """create change theme default function"""
        menu_item = self.env['ir.ui.menu'].sudo().search(
            [('parent_id', '=', False)])
        for menu in menu_item:
            if menu.name == 'Contacts':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'contacts.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Link Tracker':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'link-tracker.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Dashboards':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'dashboards.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Sales':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'sales.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Invoicing':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'accounting.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Accounting':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'accounting.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Inventory':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'inventory.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Purchase':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'purchase.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Calendar':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'calendar.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'CRM':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'crm.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Note':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'notes.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Website':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'website.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Point of Sale':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'pos.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Manufacturing':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'manufacturing.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Repairs':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'repairs.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Email Marketing':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'email-marketing.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'SMS Marketing':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'sms-marketing.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Project':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'project.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Surveys':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'surveys.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Employees':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'employee.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Recruitment':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'recruitment.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Attendances':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'attendances.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Time Off':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'timeoff.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Expenses':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'expenses.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Maintenance':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'maintenance.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Live Chat':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'live-chat.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Lunch':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'lunch.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Fleet':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'fleet.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Timesheets':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'timesheets.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Events':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'events.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'eLearning':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'elearning.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Members':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'members.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Apps':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'apps.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Discuss':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'discuss.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Settings':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img', 'icons',
                    'settinga.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})

    def icon_change_theme_green(self):
        """Create a change icon theme green"""
        menu_item = self.env['ir.ui.menu'].sudo().search(
            [('parent_id', '=', False)])
        for menu in menu_item:
            if menu.name == 'Contacts':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'contacts.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Link Tracker':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'link-tracker.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Dashboards':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'dashboards.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Sales':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'sales.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Invoicing':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'accounting.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Inventory':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'inventory.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Purchase':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'purchase.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Calendar':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'calendar.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'CRM':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'crm.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Note':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'notes.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Website':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'website.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Point of Sale':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'pos.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Manufacturing':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'manufacturing.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Repairs':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'repairs.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Email Marketing':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'email-marketing.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'SMS Marketing':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'sms-marketing.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Project':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'project.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Surveys':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'surveys.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Employees':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'employee.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Recruitment':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'recruitment.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Attendances':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'attendances.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Time Off':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'timeoff.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Expenses':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'expenses.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Maintenance':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'maintenance.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Live Chat':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'live-chat.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Lunch':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'lunch.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Fleet':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'fleet.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Timesheets':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'timesheets.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Events':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'events.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'eLearning':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'elearning.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Members':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'members.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Apps':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'apps.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Discuss':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'discuss.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Settings':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'settinga.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})
            if menu.name == 'Accounting':
                img_path = get_module_resource(
                    'vista_backend_theme', 'static', 'src', 'img',
                    'icons_green',
                    'accounting.png')
                menu.write({'web_icon_data': base64.b64encode(
                    open(img_path, "rb").read())})


class ThemeStored(models.Model):
    """create a Model ThemeStored"""
    _name = "theme.data.stored"

    name = fields.Selection([
        ('default', 'Default'),
        ('two', 'Green'),
        ('three', 'Black'),
    ], 'Theme', default='default')
