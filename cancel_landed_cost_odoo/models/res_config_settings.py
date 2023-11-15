# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    """Model for managing the configuration settings for canceling landed
    costs."""

    _inherit = "res.config.settings"

    land_cost_cancel_modes = fields.Selection([
        ('cancel', 'Cancel'),
        ('cancel_draft', 'Cancel and Reset to Draft'),
        ('cancel_delete', 'Cancel and Delete'),
    ], string='Operation Type', default='cancel',
        help="Select the operation to perform when canceling a landed cost.",
        config_parameter='cancel_landed_cost_odoo.land_cost_cancel_modes')
