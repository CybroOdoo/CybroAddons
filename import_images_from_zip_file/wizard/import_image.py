# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: NILA UJ (odoo@cybrosys.com)
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
    reference = fields.Selection(selection='_get_reference',
                                 help="Choose what type of reference the "
                                      "image files are named after",
                                 string="Based on")
    model_template = fields.Selection([
        ('product.template', "Product Template"),
        ('product.product', "Product Product"),
        ('hr.employee', "Employee"),
        ('res.partner', "Partner"),
    ], help="Choose what type of reference the image files are named after",
        string="Model Template", readonly=True)

    def _get_reference(self):
        """
        Function for retrieving the value for selection field
        :type : list(str)
        :returns: list(str)
        """
        model = self._context.get('default_model_template')
        selection = False
        if model == "product.template":
            selection = [
                ('name', "Name"),
                ('internal_reference', "Internal Reference"),
                ('barcode', "Barcode"),
            ]
        elif model == "product.product":
            selection = [
                ('internal_reference', "Internal Reference"),
                ('barcode', "Barcode"),
            ]
        elif model == "hr.employee":
            selection = [
                ('name', "Name"),
                ('identification_no', "Identification No"),
            ]
        elif model == "res.partner":
            selection = [
                ('name', "Name"),
            ]
        return selection

    def action_import(self):
        """Function for importing images
        :type : list(str)
        :returns: action definition to open wizard view
        """
        model = False
        if self.model_template:
            model = self.model_template
        if not self.reference:
            raise ValidationError(
                _('Please choose all options'))
        elif not self.file:
            raise ValidationError(
                _('Please choose a zip file'))

        file = base64.decodebytes(self.file)
        fileobject = tempfile.NamedTemporaryFile(delete=False)
        fname = fileobject.name
        fileobject.write(file)
        fileobject.close()

        file_zip = self.file
        main_file = open(fname, 'r+b')
        data = main_file.read()
        main_file.write(base64.b64decode(file_zip))
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

                for binary_image, record_reference \
                        in zip(binary_file_list, path_list):
                    if self.reference == 'name' and model != 'product.product':
                        record = self.env[model].search(
                            [('name', 'ilike', record_reference.split('.', 1)[0])])
                    if self.reference == 'internal_reference' \
                            and model != 'hr.employee':
                        record = self.env[model].search(
                            [('default_code', 'ilike', record_reference.split('.', 1)[0])])
                    if self.reference == 'barcode' and model != 'res.partner' \
                            and model != 'hr.employee':
                        record = self.env[model].search(
                            [('barcode', 'ilike', record_reference.split('.', 1)[0])])
                    if self.reference == 'identification_no' \
                            and model != 'res.partner' \
                            and model != 'product.product' \
                            and model != 'product.template':
                        record = self.env[model].search(
                            [('identification_id', 'ilike', record_reference.split('.', 1)[0])])
                    record.image_1920 = binary_image

            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except zipfile.BadZipfile:
            raise ValidationError(_('Please upload a zip file'))
