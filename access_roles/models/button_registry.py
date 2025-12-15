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


class ButtonRegistry(models.Model):
    """Class for representing buttons"""
    _name = 'button.registry'
    _description = 'Button Registry'

    name = fields.Char(string='Button Name', required=True)
    action_name = fields.Char(string='Action/Method Name')
    model_id = fields.Many2one('ir.model', string='Model', ondelete='cascade')
    view_ids = fields.Many2many('ir.ui.view', string='View')

    @api.model
    def _register_hook(self):
        """
        Hook that runs when the module is loaded.
        Calls `get_all_buttons` to populate the button registry.
        """
        super()._register_hook()
        self.get_all_buttons()
        return True

    def get_all_buttons(self):
        """Finds buttons from views and stores them."""
        views = self.env['ir.ui.view'].search([])
        button_model = {}
        # Collect buttons per model, along with the view IDs where they appear.
        for view in views:
            if view.arch:
                model_name = view.model
                if model_name not in button_model:
                    button_model[model_name] = {}
                # Find all buttons in the view XML with their attributes
                button_pattern = r'<button\s+([^>]*)>'
                buttons = re.findall(button_pattern, view.arch)
                for button_attrs in buttons:
                    name_match = re.search(r'name="([^"]*)"', button_attrs)
                    if not name_match:
                        continue
                    button_name = name_match.group(1)
                    display_name = button_name
                    string_match = re.search(r'string="([^"]*)"', button_attrs)
                    if string_match:
                        display_name = string_match.group(1)
                    else:
                        title_match = re.search(r'title="([^"]*)"', button_attrs)
                        if title_match:
                            display_name = title_match.group(1)
                    button_key = (button_name, display_name)
                    if button_key not in button_model[model_name]:
                        button_model[model_name][button_key] = []
                    if view.id not in button_model[model_name][button_key]:
                        button_model[model_name][button_key].append(view.id)
        for model_name, buttons in button_model.items():
            if not model_name or not buttons:
                continue
            model_record = self.env['ir.model'].search(
                [('model', '=', model_name)], limit=1)
            if not model_record:
                continue
            for button_info, view_ids in buttons.items():
                button_name, display_name = button_info
                existing_button = self.search([
                    ('name', '=', display_name),
                    ('action_name', '=', button_name),
                    ('model_id', '=', model_record.id)
                ], limit=1)
                if not existing_button:
                    self.create({
                        'name': display_name,
                        'action_name': button_name,
                        'model_id': model_record.id,
                        'view_ids': [Command.link(view) for view in view_ids],
                    })
        return button_model
