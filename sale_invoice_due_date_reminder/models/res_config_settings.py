# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nikhil M  (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models
conf_param = {
    'sale': 'sale_invoice_due_date_reminder.reminder_sale',
    'sale_d': 'sale_invoice_due_date_reminder.set_date_sales',
    'inv': 'sale_invoice_due_date_reminder.reminder_invoicing',
    'inv_d': 'sale_invoice_due_date_reminder.set_date_invoicing'
}


class ResConfigSettings(models.TransientModel):
    """Class for the inherited transient model res.config.settings."""
    _inherit = 'res.config.settings'

    reminder_sales = fields.Boolean(string='Reminder for Sales',
                                    help='Enable this field to get reminder '
                                         'of due in Sale Order.',
                                    config_parameter=conf_param['sale'])
    set_date_sales = fields.Integer(string='Set Days', help='Reminder'
                                    'will send according to the'
                                    'no. of days set.',
                                    config_parameter=conf_param['sale_d'])
    reminder_invoicing = fields.Boolean(string='Reminder for Invoicing',
                                        help='Enable this field to get'
                                             'reminder of due in Invoicing.',
                                        config_parameter=conf_param['inv'])
    set_date_invoicing = fields.Integer(string='Set Days',
                                        help='Reminder will send according to'
                                             'this number of days set in this'
                                             'field.',
                                        config_parameter=conf_param['inv_d'])
