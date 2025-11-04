# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
import re
from odoo import api, Command, fields, models


class TabRegistry(models.Model):
    """Class for representing tabs"""
    _name = 'tab.registry'
    _description = 'Tab Registry'

    name = fields.Char(string='Tab Name', required=True)
    view_ids = fields.Many2many('ir.ui.view', string='View')
    model_id = fields.Many2one('ir.model', string='Model', ondelete='cascade')

    @api.model
    def _register_hook(self):
        """Triggers filter extraction during module initialization."""
        super()._register_hook()
        self.get_all_tabs()
        return True

    def get_all_tabs(self):
        """Finds buttons from views and stores them."""
        views = self.env['ir.ui.view'].search([])
        tab_model = {}
        # Collect tabs per model, along with the view IDs where they appear.
        for view in views:
            if view.arch:
                model_name = view.model
                if model_name not in tab_model:
                    tab_model[model_name] = {}
                found_tabs = re.findall(r'<page[^>]*string="([^"]*)"', view.arch)
                for tab_name in found_tabs:
                    if tab_name not in tab_model[model_name]:
                        tab_model[model_name][tab_name] = []
                    if view.id not in tab_model[model_name][tab_name]:
                        tab_model[model_name][tab_name].append(view.id)
        # Create registry records for each tab.
        for model_name, tabs in tab_model.items():
            if not model_name or not tabs:
                continue
            model_record = self.env['ir.model'].search([('model', '=', model_name)],
                                                       limit=1)
            if not model_record:
                continue
            for tab_name, view_ids in tabs.items():
                existing_tab = self.search([
                    ('name', '=', tab_name),
                    ('model_id', '=', model_record.id)
                ], limit=1)
                if not existing_tab:
                    self.create({
                        'name': tab_name,
                        'model_id': model_record.id,
                        'view_ids': [Command.link(view) for view in view_ids],
                    })
        return tab_model
