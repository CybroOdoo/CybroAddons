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
from odoo import fields, models


class FileFormatSource(models.Model):
    """Store source file formats used by compression rules."""
    _name = 'source.file.format'
    _description = 'Source File Formats'

    name = fields.Char(string="Format Extension", required=True)
    mime_type = fields.Char(
        string="MIME Type",
        help="MIME types are used to identify the file type, for example "
             "image/png.",
        required=True,
        copy=False,
    )

    _mime_type_uniq = models.Constraint(
        'unique (mime_type)',
        'MIME type already exists!',
    )

    def name_get(self):
        """Return the display name of the file format."""
        result = []
        for rec in self:
            result.append((rec.id, f"{rec.name} ({rec.mime_type})"))
        return result
