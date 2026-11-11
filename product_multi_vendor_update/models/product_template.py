# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#############################################################################
from odoo import models


class ProductTemplate(models.Model):
    """ We can select multiple product and select update vendor form
        the action menu thus it returns a wizard to update details"""
    _inherit = 'product.template'

    def product_multi_vendor_update(self):
        """Return a wizard where we can enter the vendor information to be
                updated """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Vendor',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'product.vendor.update',
        }
