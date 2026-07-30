# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited the settings and add new fields"""
    _inherit = 'res.config.settings'

    is_pos_enable_keyboard_shortcuts = fields.Boolean(
        string='Enable keyboard shortcuts',
        help='Choose Keyboard Shortcut for the POS Session',
        related='pos_config_id.is_enable_keyboard_shortcuts',
        readonly=False
        )
    pos_select_shortcut_id = fields.Many2one(
        'pos.keyboard.shortcut',
        string='Choose Shortcut',
        related='pos_config_id.select_shortcut_id',
        readonly=False,
        help='To select pos keyboard shortcut'
    )
