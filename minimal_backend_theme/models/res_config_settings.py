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
#############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .global_search import SEARCH_MODELS_PARAM

PARAM_PREFIX = 'minimal_backend_theme.'
MENU_LAYOUTS = [('horizontal', 'Top bar'), ('vertical', 'Sidebar')]
BOOLEAN_OPTIONS = ('dark_mode', 'compact', 'full_width')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # The theme's display options, shared by all users. Also edited from the
    # Quick settings menu of the top bar (see minimal_theme_set_option).
    minimal_theme_menu_layout = fields.Selection(
        MENU_LAYOUTS,
        string='Menu Layout',
        default='horizontal',
        config_parameter=PARAM_PREFIX + 'menu_layout',
    )
    minimal_theme_dark_mode = fields.Boolean(
        string='Dark Mode',
        config_parameter=PARAM_PREFIX + 'dark_mode',
    )
    minimal_theme_compact = fields.Boolean(
        string='Compact View',
        config_parameter=PARAM_PREFIX + 'compact',
    )
    minimal_theme_full_width = fields.Boolean(
        string='Full-width Forms',
        config_parameter=PARAM_PREFIX + 'full_width',
    )

    # Record types the top bar search finds (stored as model names in
    # SEARCH_MODELS_PARAM; until saved once, the defaults apply).
    minimal_theme_search_model_ids = fields.Many2many(
        'ir.model',
        string='Searchable Records',
        domain=[('transient', '=', False)],
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        names = self.env['minimal_backend_theme.global_search']._get_search_model_names()
        IrModel = self.env['ir.model'].sudo()
        res['minimal_theme_search_model_ids'] = [
            fields.Command.set([IrModel._get_id(name) for name in names]),
        ]
        return res

    def set_values(self):
        super().set_values()
        names = ','.join(self.minimal_theme_search_model_ids.mapped('model'))
        self.env['ir.config_parameter'].sudo().set_str(SEARCH_MODELS_PARAM, names)

    @api.model
    def _minimal_theme_get_settings(self):
        """Theme settings as sent to the web client (see ir.http.session_info)."""
        ICP = self.env['ir.config_parameter'].sudo()
        layout = ICP.get_str(PARAM_PREFIX + 'menu_layout', 'horizontal')
        return {
            'menu_layout': layout if layout in dict(MENU_LAYOUTS) else 'horizontal',
            'dark_mode': ICP.get_bool(PARAM_PREFIX + 'dark_mode', False),
            'compact': ICP.get_bool(PARAM_PREFIX + 'compact', False),
            'full_width': ICP.get_bool(PARAM_PREFIX + 'full_width', False),
            'can_edit': self.env.user.has_group('base.group_system'),
        }

    @api.model
    def minimal_theme_set_option(self, key, value):
        """Save one display option from Quick settings: the same value the
        Settings page shows and edits. Administrators only.

        :param key: 'menu_layout', 'dark_mode', 'compact' or 'full_width'
        :param value: 'horizontal'/'vertical' for the menu layout, a boolean
            for the others
        """
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_("Only administrators can change the backend theme options."))
        ICP = self.env['ir.config_parameter'].sudo()
        if key == 'menu_layout':
            if value not in dict(MENU_LAYOUTS):
                raise ValidationError(_("Unknown menu layout: %s", value))
            ICP.set_str(PARAM_PREFIX + key, value)
        elif key in BOOLEAN_OPTIONS:
            if not isinstance(value, bool):
                raise ValidationError(_("The option %s takes true or false.", key))
            ICP.set_bool(PARAM_PREFIX + key, value)
        else:
            raise ValidationError(_("Unknown backend theme option: %s", key))
        return self._minimal_theme_get_settings()
