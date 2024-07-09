# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (<https://www.cybrosys.com>)
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
################################################################################
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
