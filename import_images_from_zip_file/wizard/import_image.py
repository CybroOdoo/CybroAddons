# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj @cybrosys(odoo@cybrosys.com)
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
import base64
import tempfile
import io
import zipfile
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImportImage(models.TransientModel):
    _name = "import.image"
    _description = 'Import Image Wizard'

    file = fields.Binary(string="Zip", help="Binary file")
    product_template_selection = fields.Selection([
        ('name', "Name"),
        ('internal_reference', "Internal Reference"),
        ('barcode', "Barcode"),
    ], string="Based On", help="Choose what type of reference the "
                               "image files are named after", )
    res_partner_selection = fields.Selection([('name', "Name")], string="Based On",
                                             help="Choose what type of reference the "
                                                  "image files are named after")
    product_product_selection = fields.Selection([('internal_reference', "Internal Reference"),
                                                  ('barcode', "Barcode")], help="Choose what type of reference the "
                                                                                "image files are named after",
                                                 string="Based on")
    hr_employee_selection = fields.Selection([('name', "Name"),
                                              ('identification_no', "Identification No")],
                                             help="Choose what type of reference the "
                                                  "image files are named after",
                                             string="Based on")
    model_template = fields.Selection([('product.template', "Product Template"), ('product.product', "Product Product"),
                                       ('hr.employee', "Employee"), ('res.partner', "Partner")],
                                      help="Choose what type of reference the image files are named after",
                                      string="Model Template", readonly=True)

    def action_import(self):
        """Function for importing images
        :type : list(str)
        :returns: action definition to open wizard view
        """
        if not self.file:
            raise ValidationError(_('Please choose a zip file'))
        model = self.model_template
        file = base64.b64decode(self.file)
        fileobject = tempfile.NamedTemporaryFile(delete=False)
        fname = fileobject.name
        fileobject.write(file)
        fileobject.close()
        main_file = open(fname, 'r+b')
        data = main_file.read()
        pos = data.find(b'\x50\x4b\x05\x06')
        main_file.seek(pos + 22)
        try:
            with zipfile.ZipFile(main_file, 'r') as zip_file:
                path_list = []
                converted_string_list = []
                for name in zip_file.namelist():
                    path_list.append(name)
                    converted_string_list.append(zip_file.read(name))
                binary_file_list = []
                for binary_file in converted_string_list:
                    binary_file_list.append(base64.b64encode
                                            (io.BytesIO(binary_file).read()))
                main_file.close()
                if self.model_template=="product.template":
                    reference = self.product_product_selection
                elif self.model_template =="product.product":
                    reference = self.product_product_selection
                elif self.model_template == "res.partner":
                    reference = self.res_partner_selection
                else:
                    reference = self.hr_employee_selection
                for binary_image, record_reference \
                        in zip(binary_file_list, path_list):
                    if reference == 'name' and model != 'product.product':
                        record = self.env[model].search(
                            [('name', 'ilike', record_reference.split('.', 1)[0])])
                    if reference == 'internal_reference' \
                            and model != 'hr.employee':
                        record = self.env[model].search(
                            [('default_code', 'ilike', record_reference.split('.', 1)[0])])
                    if reference == 'barcode' and model != 'res.partner' \
                            and model != 'hr.employee':
                        record = self.env[model].search(
                            [('barcode', 'ilike', record_reference.split('.', 1)[0])])
                    if reference == 'identification_no' \
                            and model != 'res.partner' \
                            and model != 'product.product' \
                            and model != 'product.template':
                        record = self.env[model].search(
                            [('identification_id', 'ilike', record_reference.split('.', 1)[0])])
                    for rec in record:
                        rec.image_1920 = binary_image

            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except zipfile.BadZipfile:
            raise ValidationError(_('Please upload a zip file'))
