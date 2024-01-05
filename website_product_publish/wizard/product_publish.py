# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Jumana Haseen (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models


class ProductPublish(models.TransientModel):
    """ Wizard for multiple product publish in product template """
    _name = 'product.publish'
    _description = "Product Publish/Unpublish"

    def action_product_multi_publish(self):
        """ Function for publishing products on a website """
        active_ids = self._context.get('active_ids')
        products = self.env['product.template'].browse(active_ids)
        products = products.filtered(lambda product: product.sale_ok == True)
        for product in products:
            product.is_published = True

    def action_product_multi_unpublish(self):
        """ Function for un publish product in website"""
        active_ids = self._context.get('active_ids')
        products = self.env['product.template'].browse(active_ids)
        products = products.filtered(lambda product: product.sale_ok == True)
        for product in products:
            product.is_published = False
