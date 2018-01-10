# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
import csv
import urllib2
import base64
import StringIO
import sys
from odoo import models, fields, api
from odoo.exceptions import Warning


class ProductImageImportWizard(models.TransientModel):
    _name = 'import.product_image'

    product_model = fields.Selection([('1', 'Product Template'),  ('2', 'Product Variants')], string="Product Model")
    pdt_operation = fields.Selection([('1', 'Product Creation'), ('2', 'Product Updation')], string="Product Operation")
    file = fields.Binary('File to import', required=True)

    @api.multi
    def import_file(self):
        file = StringIO.StringIO(base64.decodestring(self.file))
        reader = csv.reader(file, delimiter=',')
        csv.field_size_limit(sys.maxsize)
        skip_header = True
        for row in reader:
            if skip_header:
                skip_header = False
                continue
            product = row[0]
            image_path = row[1]
            if "http://" in image_path or "https://" in image_path:
                try:
                    link = urllib2.urlopen(image_path).read()
                    image_base64 = base64.encodestring(link)
                    if self.product_model == '1':
                        product_obj = self.env['product.template']
                    else:
                        product_obj = self.env['product.product']
                    product_id = product_obj.search([('name', '=', product)])

                    vals = {
                        'image_medium': image_base64,
                        'name': product,
                    }
                    if self.pdt_operation == '1' and not product_id:
                        product_obj.create(vals)
                    elif self.pdt_operation == '1' and product_id:
                        product_id.write(vals)
                    elif self.pdt_operation == '2' and product_id:
                        product_id.write(vals)
                    elif not product_id and self.pdt_operation == '2':
                        raise Warning("Could not find the product '%s'" % product)
                except:
                    raise Warning("Please provide correct URL for product '%s' or check your image size.!" % product)
            else:
                try:
                    with open(image_path, 'rb') as image:
                        image_base64 = image.read().encode("base64")
                        if self.product_model == '1':
                            product_obj = self.env['product.template']
                        else:
                            product_obj = self.env['product.product']
                        product_id = product_obj.search([('name', '=', product)])
                        vals = {
                            'image_medium': image_base64,
                            'name': product,
                        }
                        if self.pdt_operation == '1' and not product_id:
                            product_obj.create(vals)
                        elif self.pdt_operation == '1' and product_id:
                            product_id.write(vals)
                        elif self.pdt_operation == '2' and product_id:
                            product_id.write(vals)
                        elif not product_id and self.pdt_operation == '2':
                            raise Warning("Could not find the product '%s'" % product)
                except IOError:
                    raise Warning("Could not find the image '%s' - please make sure it is accessible to this script" %
                                  product)

