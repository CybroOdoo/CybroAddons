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

from odoo import fields,  models


class FileFormatSource(models.Model):
    """
    A model to store and manage source file formats and their corresponding
    MIME types for image compression filtering.
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
        """
        Returns a list of tuples containing the record ID and a display name
        formatted as 'name (mime_type)'.
        """
        result = []
        for rec in self:
            result.append((rec.id, rec.name + " (" + rec.mime_type + ")"))
        return result
