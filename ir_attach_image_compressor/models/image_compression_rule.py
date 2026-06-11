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

import base64
import logging
import os
from datetime import datetime, timedelta

from odoo import models, fields
from odoo.osv import expression
from odoo.tools import image_process

_logger = logging.getLogger(__name__)

mimetypes_global = [
    'image/avif',
    'image/bmp',
    'image/gif',
    'image/x-gif',
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
    'image/x-xwindowdump'
]

DESTINATION_MIMETYPES = {
    'JPEG': 'image/jpeg',
    'PNG': 'image/png',
    'GIF': 'image/gif',
    'ICO': 'image/x-icon'
}


class ImageCompressor(models.Model):
    """
    Defines rules for automatic image compression of attachments.
    Allows specifying models, source formats, quality, and destination formats.
    """
    _name = "ir.image.compressor.rule"
    _description = "ir_Image_Compressor_Rule"

    name = fields.Char(string="Name", required=True,
                       help="Name of the image compression rule.")
    af_model_ids = fields.Many2many(
        "ir.model", string="Model(s)", required=True,
        help="Select the models to which this compression rule applies.")
    source_format_ids = fields.Many2many(
        "source.file.format", string="Source Format",
        help="Specific source formats to compress.")
    quality = fields.Integer(
        string="Quality", help="Quality percentage of the compressed image.")
    destination_format = fields.Selection([
        ('JPEG', '.jpeg'),
        ('PNG', '.png'),
        ('GIF', '.gif'),
        ('ICO', '.ico')
    ], string="Destination format", default='JPEG', required=True,
        help="The target format for the compressed images.")
    active = fields.Boolean(
        string="Active", help="Archive or unarchive the rule.")
    minimum_size = fields.Integer(
        string="Minimum Size(KB)",
        help="Only compress images larger than this size in KB.")
    older_days = fields.Integer(
        string="Older than(days)",
        help="Only compress images older than this many days.")

    def _get_attachments_domain(self, model_names):
        """
        Constructs a domain to search for attachments based on the rule's criteria
        such as model names, source formats, minimum size, and age.
        """
        all_mime_types = list(set(mimetypes_global).union(
            set(self.env['source.file.format'].sudo().
                search([]).mapped('mime_type'))))

        if not self.source_format_ids:
            domains = [('mimetype', 'in', all_mime_types)]
        else:
            sr_fmts = self.source_format_ids.mapped('mime_type')
            domains = [('mimetype', 'in', sr_fmts)]

        if model_names:
            domains = expression.AND(
                [domains, [('res_model', 'in', model_names)]])

        if self.minimum_size:
            domains = expression.AND(
                [domains, [('file_size', '>', self.minimum_size * 1024)]])

        if self.older_days:
            old_day = datetime.now() + timedelta(days=-self.older_days)
            domains = expression.AND(
                [domains, [('create_date', '<', old_day)]])

        return domains

    def _schedule_auto_compress(self):
        """
        Cron job method that iterates through active compression rules and
        processes matching attachments.
        """
        i_c_rules = self.env['ir.image.compressor.rule'].\
            search([('active', '=', True)])

        for record in i_c_rules:
            res_models = record.af_model_ids
            model_names = res_models.mapped('model')
            attach_ments = self.env['ir.attachment'].search(
                record._get_attachments_domain(model_names))

            for rec in attach_ments:
                try:
                    if rec.raw:
                        img_payload = rec.raw
                    else:
                        if not rec.datas:
                            continue
                        img_payload = base64.b64decode(rec.datas)

                    quality = int(record.quality if record.quality else 95)

                    if record.destination_format:
                        image_data = image_process(
                            img_payload,
                            verify_resolution=False,
                            quality=quality,
                            output_format=record.destination_format
                        )
                    else:
                        image_data = image_process(
                            img_payload,
                            verify_resolution=False,
                            quality=quality
                        )

                    if rec.raw:
                        rec.raw = image_data
                    else:
                        rec.datas = base64.b64encode(image_data)

                    if record.destination_format:
                        base = os.path.splitext(rec.name)[0]
                        dest_format_sel = dict(
                            record._fields['destination_format'].selection
                        )
                        rec.name = base + dest_format_sel.get(
                            record.destination_format
                        )
                        rec.mimetype = DESTINATION_MIMETYPES.get(
                            record.destination_format
                        )
                except Exception as e:
                    _logger.warning(
                        "Failed to compress image attachment %s: %s",
                        rec.id, str(e)
                    )
                    continue
