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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields


class FileFormatSource(models.Model):
    """Catalogue of source image file formats.

    Stores the file extension and its mime type so that compression rules
    can target specific source formats of ``ir.attachment`` records.
    """
    _name = 'source.file.format'
    _description = 'Source File Formats'

    name = fields.Char(string="Format Extension", required=True,
                       help="Extension of the file format, e.g. .png")
    mime_type = fields.Char(
        string="Mime Type",
        help="Mime types are used to identify the file type. "
             "The format is something like image/png",
        required=True,
        copy=False)

    _sql_constraints = [
        ('unique_mime_type', 'unique (mime_type)', 'Mime type already exists!')
    ]

    def name_get(self):
        """Display the format as ``name (mime_type)`` in the UI."""
        result = []
        for rec in self:
            result.append((rec.id, rec.name + " (" + rec.mime_type + ")"))
        return result
