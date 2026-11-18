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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Extend configuration settings to manage the package split feature."""

    _inherit = 'res.config.settings'

    enable_package_split = fields.Boolean(
        string='Package Split',
        config_parameter='package_split.enable_package_split',
        compute='_compute_enable_package_split',
        readonly=False,
        store=True,
        help="Enable package split feature",
    )

    @api.depends('group_stock_tracking_lot')
    def _compute_enable_package_split(self):
        """Automatically enable package split when packages tracking is enabled."""
        for record in self:
            record.enable_package_split = record.group_stock_tracking_lot
