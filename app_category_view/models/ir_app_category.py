"""Modle for app category"""
# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul  (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class IrAppCategory(models.Model):
    """
       Model representing the category of installed apps in the home menu.
    """
    _name = 'ir.app.category'
    _description = 'category'

    name = fields.Char(string='Name', help='Enter category name')
    installed_apps_ids = fields.Many2many('ir.ui.menu',
                                          string='Apps Installed',
                                          domain=[('parent_id', '=', False)],
                                          help="You can add the installed apps "
                                               "to display under the category "
                                               "here", required=True)
    sequence = fields.Integer(string="Sequence", help='Number sequence')

    @api.constrains('name')
    def name_check(self):
        """Check the same category name"""
        names = self.env['ir.app.category'].search([]).mapped('name')
        print(names)
        if self.name in names:
            existing_category = self.search([('name', '=', self.name)])
            if len(existing_category) > 1:
                raise UserError(
                    _('Try different name,Already a category in this name'))
            else:
                pass

    @api.model
    def create(self, vals):
        """The `sequence` field will be automatically set to the next value in
         the 'ir.sequence' sequence for 'ir.app.category.'

        :param vals: A dictionary of field values for the new record
        :return: the new 'ir.app.category' Creates a new app category record.
        """
        vals['sequence'] = self.env['ir.sequence'].next_by_code(
            'ir.app.category')
        return super(IrAppCategory, self).create(vals)

    @api.model
    def get_home_dashboard(self):
        """Return the home dashboard configuration as a list of dictionaries.

        Each dictionary contains information about a category, including its
        name and the IDs of the installed apps associated with it. The
        categories are sorted by their sequence attribute.
        Returns:
            list: A list of dictionaries containing category information.
        """
        categories = self.env['ir.app.category'].search([], order='sequence')
        return [{'name': record.name,
                 'installed_apps': record.installed_apps_ids.ids} for record in
                categories]

    @api.model
    def get_other_apps(self):
        """Retrieve the IDs of apps that are not assigned to any category.
        Returns:
            list: List of IDs unassigned apps.
        """
        installed_apps = self.env['ir.app.category'].search(
            []).installed_apps_ids.ids
        return self.env['ir.ui.menu'].search(
            [('id', 'not in', installed_apps), ('parent_id', '=', False)]).ids

    @api.model
    def apps_switching(self, menu_1, menu_2):
        """Switches the sequence of two app menu items."""
        menu_item_1 = self.env['ir.ui.menu'].browse(int(menu_1))
        menu_item_2 = self.env['ir.ui.menu'].browse(int(menu_2))
        menu_item_1.sequence, menu_item_2.sequence = menu_item_2.sequence, menu_item_1.sequence

    @api.model
    def category_change(self, menu_id, category_name):
        """Moves an app from its current category to a new category."""
        current_category = self.env['ir.app.category'].search(
            [('installed_apps_ids', 'in', int(menu_id))])
        if category_name != 'OtherApps':
            category_id = self.env['ir.app.category'].search(
                [('name', '=', category_name)])
            if category_id:
                if current_category:
                    current_category.write(
                        {'installed_apps_ids': [(3, int(menu_id))]})
                category_id.write({'installed_apps_ids': [(4, int(menu_id))]})
            elif current_category:
                current_category.write(
                    {'installed_apps_ids': [(3, int(menu_id))]})
        else:
            current_category.write({'installed_apps_ids': [(3, int(menu_id))]})
