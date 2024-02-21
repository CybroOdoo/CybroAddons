# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
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
###############################################################################
from datetime import timedelta
from odoo import fields, http
from odoo.http import request


class DeliveryDateScheduler(http.Controller):
    """Add lawyers as selection values in Dashboard"""

    @http.route('/delivery_date_schedule', type='json', auth='user',
                csrf=False)
    def delivery_date_schedule(self, **kw):
        """
        for checking the user entered delivery date
        """
        config_parameter = request.env['ir.config_parameter']
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
            if minimum_date < fields.Date.from_string(
                    kw.get('date')) < maximum_date:
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

    @http.route('/confirm_delivery_date_schedule', type='json', auth='user',
                csrf=False)
    def confirm_delivery_date_schedule(self, **kw):
        """
        confirm and writing the confirmed quotation
        """
        sale_order = request.env['sale.order'].sudo().browse(int(kw.get('id')))
        sale_order.sudo().update({
            'commitment_date': kw.get('date'),
            'user_description': kw.get('description')
        })
        sale_order.action_confirm()
