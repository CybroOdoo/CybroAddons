# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhammed Muflih c(odoo@cybrosys.com)
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
from odoo import api, fields, models

class MediaAsset(models.Model):
    _name = 'media.asset'
    _description = 'Media Assets store'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string="Name", tracking=True,
        help="The title or name of the media asset.")
    description = fields.Text(string="Description", tracking=True,
        help="Additional details or notes about this media asset.")
    media_type = fields.Selection(
        [('image', 'Image'), ('video', 'Video'), ('document', 'Document'),
         ('audio', 'Audio'), ('url', 'Url')],
        string="Media Type", tracking=True, required=True,
        help="The type of media content: Image, Video, Document, Audio, or URL.",
    )
    file = fields.Binary(string="File", attachment=True,
        help="Upload the media file. Supported formats depend on the media type selected.")
    file_name = fields.Char(
        string="Original File Name",
        tracking=True,
        readonly=True,
        help="Auto-filled from the uploaded file name. Clear the file to reset.",
    )
    file_size = fields.Float(
        string="File Size (MB)",
        compute='_compute_file_size',
        store=True,
        readonly=True,
        digits=(16, 3),
        tracking=True,
        help="File size in megabytes. Automatically computed when a file is uploaded.",
    )
    source_url = fields.Char(string="Source URL", tracking=True,
        help="External URL for the media asset when source type is set to URL.")
    category_id = fields.Many2one(
        comodel_name='media.category',
        string="Media Category",
        ondelete='set null',
        tracking=True,
        help="Category used to organise and group related media assets.",
    )
    source_type = fields.Selection(
        [('file', 'File'), ('url', 'Url')],
        string="Source Type", tracking=True, default="file",
        help="Choose whether to upload a file or provide an external URL.",
    )
    create_uid = fields.Many2one(comodel_name='res.users', string="Uploaded By", readonly=True, tracking=True,
        default=lambda self: self.env.uid,
        help="The user who uploaded or created this media asset.")
    create_date = fields.Datetime(string="Upload Date", readonly=True, default=fields.Date.today,
        help="Date and time when this media asset was first uploaded.")
    favorite = fields.Boolean(string="Favorite", tracking=True, default=False,
        help="Mark this asset as a favourite for quick access.")
    media_tag_ids = fields.Many2many(comodel_name='media.tag', string="Tags",
        help="Tags to label and classify this media asset for easier searching.")
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], default='draft', tracking=True,
        help="Draft: asset is pending review. Confirmed: asset has been approved and is active.")

    @api.model
    def get_media_type_data(self):
        """Get all records from this model and groups based on media type and return to the orm call"""
        assets = self.search([])
        image = len(assets.filtered(lambda rec: rec.media_type=='image'))
        video = len(assets.filtered(lambda rec: rec.media_type=='video'))
        document = len(assets.filtered(lambda rec: rec.media_type=='document'))
        url = len(assets.filtered(lambda rec: rec.media_type=='url'))
        audio = len(assets.filtered(lambda rec: rec.media_type=='audio'))

        return {
            'count': [image, video, document, url, audio],
            'name':['Image', 'Video', 'Document', 'Url', 'Audio']
        }


    @api.depends('file', 'source_type')
    def _compute_file_size(self):
        """Compute file size in MB by reading directly from ir.attachment.
        Avoids reading the Binary field (attachment=True) which may not be
        in the ORM cache during recomputation, causing the size to reset to 0.
        """
        IrAttachment = self.env['ir.attachment'].sudo()
        for rec in self:
            if rec.source_type == 'file' and rec.id:
                attachment = IrAttachment.search([
                    ('res_model', '=', self._name),
                    ('res_field', '=', 'file'),
                    ('res_id', '=', rec.id),
                ], limit=1)
                rec.file_size = (attachment.file_size or 0) / (1024.0 * 1024.0)
            else:
                rec.file_size = 0.0

    @api.onchange('file')
    def _onchange_file(self):
        """Clear file_name and reset file_size when the binary file is removed.
        When a file IS selected in the browser, Odoo's Binary widget
        automatically writes the original filename into file_name via the
        'filename' attribute declared on the widget in the view.
        """
        if not self.file:
            self.file_name = False
            self.file_size = 0.0

    def confirm(self):
        """ Confirm the file has been uploaded."""
        if self.state == 'draft':
            self.state = 'confirmed'