# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina P (odoo@cybrosys.com)
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
from odoo import fields, models
from io import BytesIO
from PyPDF2 import PdfFileWriter, PdfFileReader


class IrActionsReportInherit(models.Model):
    """The Class Inherits to update the fields and functions"""
    _inherit = 'ir.actions.report'

    is_password = fields.Boolean("Enable Password?",
                                 help="Activate this field if you want to add "
                                      "the password for pdf report")
    password_name = fields.Char("Password", help="Enter the Password "
                                                 "here")
    # Encrypts the given PDF data with a specified password if
    # the password protection is enabled.
    def apply_password_protection(self, pdf_content, pwd):
        """Method Added to Implement the pasword options"""
        input_buffer = BytesIO(pdf_content)
        reader = PdfFileReader(input_buffer)
        writer = PdfFileWriter()
        writer.appendPagesFromReader(reader)
        if self.is_password:
            writer.encrypt(user_pwd=self.password_name, owner_pwd=None,
                           use_128bit=True)
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer.read()
