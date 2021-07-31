# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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

from odoo import api, models


class ProductCatalogueReport(models.AbstractModel):
    """ Model to contain the information related to printing the information about
    the products"""

    _name = "report.product_catalogue.report_product_catalog"


    @api.model
    def _get_report_values(self, docids, data=None):
        """Get the report values.
                        :param : model
                        :param : docids
                        :param : data
                        :return : data
                        :return : Product template records"""
        product = self.env['product.template'].browse(docids)
        print("product............", product)
        return {
            'data': data,
            'docs': product,
        }

    # @api.model
    # def get_website_report_values(self, variant_ids, product_id):
    #     print(variant_ids, product_id, "self")
    #
    #     product_id = self.env['product.template'].search([('id', '=', product_id)])
    #     variant_ids = self.env['product.product'].search([('id', '=', variant_ids)])
    #     print(product_id, variant_ids, "self")
    #     return {
    #         'variants': variant_ids,
    #         'product': product_id,
    #     }

