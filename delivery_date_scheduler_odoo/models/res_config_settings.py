# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V(odoo@cybrosys.com)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    fields included super set_values and get_values and checking the user
    entered delivery date
    """
    _inherit = 'res.config.settings'

    warning_date = fields.Boolean(string="Restrict Date",
                                  config_parameter="delivery_date_scheduler_odoo."
                                                   "warning_date",
                                  help="You can set date range for your "
                                       "customer delivery date")
    min_date_range = fields.Integer(string="Minimum Range", default=5,
                                    required=True,
                                    config_parameter="delivery_date_scheduler_odoo."
                                                     "min_date_range",
                                    help="Set minimum date range")
    max_date_range = fields.Integer(string="Maximum Range", default=10,
                                    required=True,
                                    config_parameter="delivery_date_scheduler_odoo."
                                                     "max_date_range",
                                    help="Set maximum date range")
