# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import fields, models


class ResConfiqSettingInherit(models.TransientModel):
    _inherit = "res.config.settings"
    out_of_stock = fields.Boolean(config_parameter='inventory_stock_dashboard_odoo.out_of_stock')
    out_of_stock_quantity = fields.Integer(string="Quantity",
                                           config_parameter='inventory_stock_dashboard_odoo.out_of_stock_quantity',
                                           required=True)
    dead_stock_bol = fields.Boolean(string="Dead Stock",
                                    config_parameter='inventory_stock_dashboard_odoo.dead_stock_bol')
    dead_stock = fields.Integer(config_parameter='inventory_stock_dashboard_odoo.dead_stock', required=True)
    dead_stock_type = fields.Selection([('day', 'Day'), ('week', 'Week'), ('month', 'Month')],
                                       string="Type", default='day',
                                       config_parameter='inventory_stock_dashboard_odoo.dead_stock_type', required=True)
