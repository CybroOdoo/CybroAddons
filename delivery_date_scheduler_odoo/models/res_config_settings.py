# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
from datetime import timedelta
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """
    fields included super set_values and get_values and checking the user
    entered delivery date
    """
    _inherit = 'res.config.settings'

    warning_date = fields.Boolean(string="Restrict Date",
                                  help="You can set date range for your "
                                       "customer delivery date")
    min_date_range = fields.Integer(string="Minimum Range", default=5,
                                    required=True,
                                    help="Set minimum date range")
    max_date_range = fields.Integer(string="Maximum Range", default=10, required=True,
                                    help="Set maximum date range")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'delivery_date_scheduler_odoo.warning_date', self.warning_date)
        self.env['ir.config_parameter'].set_param(
            'delivery_date_scheduler_odoo.min_date_range', self.min_date_range)
        self.env['ir.config_parameter'].set_param(
            'delivery_date_scheduler_odoo.max_date_range', self.max_date_range)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            warning_date=params.get_param(
                'delivery_date_scheduler_odoo.warning_date'),
            min_date_range=params.get_param(
                'delivery_date_scheduler_odoo.min_date_range'),
            max_date_range=params.get_param(
                'delivery_date_scheduler_odoo.max_date_range'),
        )
        return res

    def delivery_date_schedule(self, data):
        """
        for checking the user entered delivery date
        """
        config_parameter = self.env['ir.config_parameter']
        warning_date = bool(config_parameter.sudo().get_param(
            'delivery_date_scheduler_odoo.warning_date'))
        new_maximum_date = False
        new_minimum_date = False
        if warning_date:
            min_date = int(config_parameter.sudo().get_param(
                'delivery_date_scheduler_odoo.min_date_range'))
            max_date = int(config_parameter.sudo().get_param(
                'delivery_date_scheduler_odoo.max_date_range'))
            today_date = fields.Date.today()
            minimum_date = today_date + timedelta(days=min_date)
            maximum_date = today_date + timedelta(days=max_date)
            new_maximum_date = maximum_date.strftime("%d-%m-%Y")
            new_minimum_date = minimum_date.strftime("%d-%m-%Y")
            if minimum_date < fields.Date.from_string(data) < maximum_date:
                error_value = 1
            else:
                error_value = 2
        else:
            error_value = 3
        return {
            'error_value': error_value,
            'min_date': new_minimum_date,
            'max_date': new_maximum_date
        }
