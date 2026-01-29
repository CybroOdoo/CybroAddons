# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class ResConfigSettings(models.TransientModel):
    """ Inheriting configuration settings for adding fields that indicate
        which data to import"""
    _inherit = 'res.config.settings'

    import_bom = fields.Boolean(string="Import BoM",
                                config_parameter='import_dashboard.import_bom',
                                help='For importing bom files')
    import_pos = fields.Boolean(string="Import POS",
                                config_parameter='import_dashboard.import_pos',
                                help='For importing pos')
    import_attendance = fields.Boolean(string="Import Attendance",
                                       config_parameter='import_dashboard.import_attendance',
                                       help='For importing attendance')
    import_payment = fields.Boolean(string="Import Payments",
                                    config_parameter='import_dashboard.import_payment',
                                    help='For importing payments')
    import_task = fields.Boolean(string="Import Task",
                                 config_parameter='import_dashboard.import_task',
                                 help='For importing tasks')
    import_sale = fields.Boolean(string="Import Sale",
                                 config_parameter='import_dashboard.import_sale',
                                 help='For importing sales orders')
    import_purchase_order = fields.Boolean(string="Import Purchase Order",
                                           config_parameter='import_dashboard.import_purchase_order',
                                           help='For importing purchase orders')
    import_product_template = fields.Boolean(string="Import Products",
                                             config_parameter='import_dashboard.import_product_template',
                                             help='For importing Products')
    import_partner = fields.Boolean(string="Import Partner",
                                    config_parameter='import_dashboard.import_partner',
                                    help='For importing partners')
    import_invoice = fields.Boolean(string="Import Invoice",
                                    config_parameter='import_dashboard.import_invoice',
                                    help='For importing invoices')
    import_pricelist = fields.Boolean(string="Import Pricelist",
                                      config_parameter='import_dashboard.import_pricelist',
                                      help='For importing price lists')
    import_vendor_pricelist = fields.Boolean(string="Import Vendor Pricelist",
                                             config_parameter='import_dashboard.import_vendor_pricelist',
                                             help='For importing vendor price '
                                                  'lists')
