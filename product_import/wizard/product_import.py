# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali VP (odoo@cybrosys.com)
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
import tempfile
import base64
import certifi
import urllib3
import openpyxl
from odoo.exceptions import UserError
from odoo import fields, models
from odoo.tools import _


class ProductImport(models.Model):
    """ Import Product data """
    _name = 'product.import'
    _description = 'Product Import'

    file = fields.Binary(string="Upload File", help="Choose the file to upload")
    file_name = fields.Char(string="File Name", help="Name of the file")
    option = fields.Selection([
        ('csv', 'CSV'),
        ('xlsx', 'XLSX')], default='csv', help="Choose the file type")

    def import_file(self):
        """ Function to import product details from csv or xlsx file """
        if self.option == 'csv':
            try:
                product_temp_data = self.env['product.template'].search([])
                file = base64.b64decode(self.file)
                file_string = file.decode('utf-8')
                file_string = file_string.split('\n')
                http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                           ca_certs=certifi.where())
            except:
                raise UserError(_("Please choose the correct file!"))
            firstline = True
            for file_item in file_string:
                if firstline:
                    firstline = False
                    continue
                product_temp = self.env['product.template'].search(
                    [('name', '=', file_item.split(",")[0])], limit=0)
                if not product_temp.id:
                    if file_item.split(",")[0]:
                        if ("http://" in file_item.split(",")[4] or "https://"
                                in file_item.split(",")[4]):
                            link = file_item.split(",")[4]
                            image_response = http.request('GET', link)
                            image_thumbnail = base64.b64encode(
                                image_response.data)
                            product_name = {
                                'name': file_item.split(",")[0],
                                'type': file_item.split(",")[1],
                                'barcode': file_item.split(",")[2],
                                'list_price': file_item.split(",")[3],
                                'image_1920': image_thumbnail,
                            }
                            product_temp_data.create(product_name)
                        elif '/home' in file_item.split(",")[4]:
                            with open(file_item.split(",")[4], 'rb') as file:
                                data = base64.b64encode(file.read())
                                product_name = {
                                    'name': file_item.split(",")[0],
                                    'type': file_item.split(",")[1],
                                    'barcode': file_item.split(",")[2],
                                    'list_price': file_item.split(",")[3],
                                    'image_1920': data,
                                }
                                product_temp_data.create(product_name)
                        else:
                            product_name = {
                                'name': file_item.split(",")[0],
                                'type': file_item.split(",")[1],
                                'barcode': file_item.split(",")[2],
                                'list_price': file_item.split(",")[3],
                            }
                            product_temp_data.create(product_name)
                else:
                    raise UserError(_("Add the product which is not available"
                                      "in products"))
        if self.option == 'xlsx':
            try:
                product_temp_data = self.env['product.template'].search([])

                file_string = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
                file_string.write(base64.b64decode(self.file))
                file_string.flush()
                book = openpyxl.load_workbook(file_string.name, data_only=True)
                sheet = book.active
                http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                           ca_certs=certifi.where())

            except Exception as e:
                raise UserError(_("Please choose the correct file: %s") % str(e))

            startline = True
            for row in sheet.iter_rows(values_only=True):
                if startline:
                    startline = False
                    continue

                line = list(row)
                if not line or not line[0]:
                    continue

                product_temp = self.env['product.template'].search(
                    [('name', '=', line[0])], limit=1)

                if not product_temp:
                    if line[4] and ("http://" in line[4] or "https://" in line[4]):
                        link = line[4]
                        image_response = http.request('GET', link)
                        image_thumbnail = base64.b64encode(image_response.data)
                        product_name = {
                            'name': line[0],
                            'type': line[1],
                            'barcode': line[2],
                            'list_price': line[3],
                            'image_1920': image_thumbnail,
                        }
                        product_temp_data.create(product_name)

                    # Image from local path (/home/…)
                    elif line[4] and "/home" in line[4]:
                        with open(line[4], 'rb') as file:
                            data = base64.b64encode(file.read())
                        product_name = {
                            'name': line[0],
                            'type': line[1],
                            'barcode': line[2],
                            'list_price': line[3],
                            'image_1920': data,
                        }
                        product_temp_data.create(product_name)

                    else:
                        product_name = {
                            'name': line[0],
                            'type': line[1],
                            'barcode': line[2],
                            'list_price': line[3],
                        }
                        product_temp_data.create(product_name)

                else:
                    raise UserError(_("Add the product which is not available in products"))
