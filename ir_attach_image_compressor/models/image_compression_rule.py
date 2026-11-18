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
import os
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain
from odoo.tools.image import ImageProcess

mimetypes_global = [
    'image/avif',
    'image/bmp',
    'image/gif',
    'image/ief',
    'image/jpeg',
    'image/heic',
    'image/heif',
    'image/png',
    'image/svg+xml',
    'image/tiff',
    'image/vnd.microsoft.icon',
    'image/x-cmu-raster',
    'image/x-portable-anymap',
    'image/x-portable-bitmap',
    'image/x-portable-graymap',
    'image/x-portable-pixmap',
    'image/x-rgb',
    'image/x-xbitmap',
    'image/x-xpixmap',
    'image/x-ms-bmp',
    'image/x-xwindowdump',
]


class ImageCompressor(models.Model):
    """Store compression rules applied to attachments."""
    _name = "ir.image.compressor.rule"
    _description = "Image Compression Rule"

    name = fields.Char(string="Name", required=True)
    af_model_ids = fields.Many2many(
        "ir.model",
        string="Model(s)",
        required=True,
        help="Models where this rule is applied.",
    )
    source_format_ids = fields.Many2many(
        "source.file.format",
        string="Source Format",
        help="File formats of the attachments to which this rule is applied.",
    )
    quality = fields.Integer(
        string="Quality",
        help="Quality level of the compressed image in percentage. If left "
             "empty, 95% will be used as the default value. For JPEG, 1 is "
             "the lowest and 95 is the highest recommended value. For PNG, "
             "leave empty to prevent conversion to a WEB palette.",
    )
    destination_format = fields.Selection(
        [('JPEG', '.jpeg'),
         ('PNG', '.png'),
         ('GIF', '.gif'),
         ('ICO', '.ico')],
        string="Destination Format",
        default='JPEG',
        required=True,
        help="Format to which the source files are converted or compressed.",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether the rule is active or inactive.",
    )
    minimum_size = fields.Integer(
        string="Minimum Size (KB)",
        help="Minimum size of the attachment file in KB for the rule to be "
             "applied.",
    )
    older_days = fields.Integer(
        string="Older Than (days)",
        help="Age of the attachment in days for this rule to be applied.",
    )
    allow_recompress = fields.Boolean(
        string="Recompress",
        default=False,
        help="Whether to compress already compressed attachments.",
    )

    @api.constrains('quality')
    def _check_quality(self):
        for rule in self:
            if rule.quality and not 1 <= rule.quality <= 95:
                raise ValidationError(
                    _('The quality value should be between 1 and 95.'),
                )

    def _get_attachments_domain(self, model_names):
        """Generate a dynamic attachment domain based on the rule."""
        all_mime_types = list(
            set(mimetypes_global).union(
                set(self.env['source.file.format'].sudo().
                    search([]).mapped('mime_type')),
            ),
        )
        if not self.source_format_ids:
            domains = [('mimetype', 'in', all_mime_types)]
        else:
            domains = [
                ('mimetype', 'in', self.source_format_ids.mapped('mime_type')),
            ]
        if model_names:
            domains = Domain.AND([domains, [('res_model', 'in', model_names)]])
        if self.minimum_size:
            domains = Domain.AND(
                [domains, [('file_size', '>', self.minimum_size * 1024)]],
            )
        if self.older_days:
            old_day = datetime.now() + timedelta(days=-self.older_days)
            domains = Domain.AND(
                [domains, [('create_date', '<', old_day)]],
            )
        if not self.allow_recompress:
            domains = Domain.AND([domains, [('is_compressed', '=', False)]])
        return domains

    def _schedule_auto_compress(self):
        """Compress or convert attachments and replace the source files."""
        rules = self.env['ir.image.compressor.rule'].search(
            [('active', '=', True)],
        )
        for rule in rules:
            model_names = rule.af_model_ids.mapped('model')
            attachments = self.env['ir.attachment'].search(
                rule._get_attachments_domain(model_names),
            )
            quality = int(rule.quality or 95)
            for attachment in attachments:
                if not attachment.raw:
                    continue
                image = ImageProcess(attachment.raw, verify_resolution=False)
                image_data = image.image_quality(
                    quality=quality,
                    output_format=rule.destination_format,
                )
                if not image_data:
                    continue
                attachment.raw = image_data
                attachment.is_compressed = True
                if rule.destination_format:
                    base = os.path.splitext(attachment.name)[0]
                    extension = dict(
                        rule._fields['destination_format'].selection,
                    ).get(rule.destination_format)
                    if extension:
                        attachment.name = base + extension
