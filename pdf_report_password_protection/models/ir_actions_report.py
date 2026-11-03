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
from io import BytesIO
from odoo.tools.pdf import PdfReader, PdfWriter


class IrActionsReportInherit(models.Model):
    """Add password protection fields and methods to report actions."""
    _inherit = 'ir.actions.report'

    is_password = fields.Boolean("Enable Password?",
                                 help="Activate this field if you want to add "
                                      "a password to the PDF report.")
    password_name = fields.Char("Password", help="Enter the password here.")
    # Encrypts the given PDF data with a specified password if
    # the password protection is enabled.
    def apply_password_protection(self, pdf_content, pwd):
        """Encrypt the PDF with the report password, if enabled."""
        input_buffer = BytesIO(pdf_content)
        reader = PdfReader(input_buffer)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        if self.is_password:
            writer.encrypt(self.password_name, None, True)
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer.read()
