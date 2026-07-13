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


class DashboardCustomFilter(models.Model):
    """Model to store custom backend domains for dashboard cards."""
    _name = 'dashboard.custom.filter'
    _description = 'Dashboard Custom Filter'

    name = fields.Char(
        string='Filter Label',
        required=True,
        help='Label for the custom filter.'
    )
    dashboard_menu_id = fields.Many2one(
        'dashboard.menu',
        string='Dashboard',
        ondelete='cascade',
        required=True,
        help='Dashboard this filter belongs to.'
    )
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        help='Model to apply the filter on.'
    )
    model_name = fields.Char(
        related='model_id.model',
        string='Model Name',
        store=True,
        help='Technical name of the model.'
    )
    domain = fields.Char(
        string='Domain Field',
        required=True,
        default='[]',
        help='Domain to apply for this filter.'
    )
