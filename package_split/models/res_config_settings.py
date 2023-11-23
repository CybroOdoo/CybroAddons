# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Inhering to Add a field to enable Package split"""
    _inherit = 'res.config.settings'

    enable_package_split = fields.Boolean(
        string='Package Split',
        config_parameter='package_split.enable_package_split',
        compute='_compute_enable_package_split',
        help="Enable package split feature")

    @api.depends('group_stock_tracking_lot')
    def _compute_enable_package_split(self):
        """on enabling packages it enables the field enable_package_split"""
        self.enable_package_split = self.group_stock_tracking_lot
