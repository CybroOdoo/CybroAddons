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
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ Model for enable import options in settings. """
    _inherit = 'res.config.settings'

    import_bom = fields.Boolean(
        config_parameter='import_dashboard.import_bom',
        help='For importing bills of materials', string="Import Bills of Materials")
    import_pos = fields.Boolean(
        config_parameter='import_dashboard.import_pos',
        help='For importing POS orders', string="Import POS")
    import_attendance = fields.Boolean(
        help='For importing attendance',
        config_parameter='import_dashboard.import_attendance')
    import_payment = fields.Boolean(
        help='For importing payments', config_parameter='import_dashboard.import_payment')
    import_task = fields.Boolean(
        help='For importing tasks',
        config_parameter='import_dashboard.import_task', )
    import_sale = fields.Boolean(
        help='For importing sales orders',
        config_parameter='import_dashboard.import_sale')
    import_purchase_order = fields.Boolean(
        config_parameter='import_dashboard.import_purchase_order',
        help='For importing purchase orders')
    import_product_template = fields.Boolean(
        help='For importing products',
        config_parameter='import_dashboard.import_product_template')
    import_partner = fields.Boolean(
        help='For importing partners',
        config_parameter='import_dashboard.import_partner')
    import_invoice = fields.Boolean(
        string="Import Invoices", help='For importing invoices',
        config_parameter='import_dashboard.import_invoice')
    import_pricelist = fields.Boolean(
        help='For importing price lists',
        config_parameter='import_dashboard.import_pricelist')
    import_vendor_pricelist = fields.Boolean(
        config_parameter='import_dashboard.import_vendor_pricelist',
        help='For importing vendor price lists')

