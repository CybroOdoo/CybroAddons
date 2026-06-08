# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models, fields, api, _


class ExcalidrawAttachWizard(models.TransientModel):
    """Wizard to select the type of the file and records to attach the Drawings"""
    _name = 'excalidraw.attach.wizard'
    _description = 'Attach Sketch to Record'

    sketch_data = fields.Binary(string="Sketch", required=True)
    attachment_type = fields.Selection([
        ('image', 'Image (PNG)'),
        ('pdf', 'PDF Document'),
        ('excel', 'Excel Spreadsheet'),
        ('word', 'Word Document')
    ], string="Attachment Type", default='image', required=True)
    model_id = fields.Many2one(
        'ir.model', string="Model", required=True,
        domain=lambda self: [('model', 'in', self._get_chatter_models())]
    )
    model_name = fields.Char(related='model_id.model', readonly=True)
    res_id = fields.Many2oneReference(
        model_field='model_name', string="Record", required=True
    )

    @api.model
    def _get_chatter_models(self):
        """Identify standard business models where chatter/mail thread is active and writeable"""
        allowed_models = []
        excluded_prefixes = ('ir.', 'web.', 'bus.', 'report.', 'base_import.', 'digest.', 'utm.', 'base.', 'mail.')
        for model_name, model_class in self.env.registry.items():
            # Exclude transient, abstract or standard Odoo technical/system models
            if model_class._transient or model_class._abstract:
                continue
            if 'message_ids' not in model_class._fields:
                continue
            # Filter internal technical namespaces unless they are key business objects (like res.partner/res.users)
            if model_name.startswith(excluded_prefixes) and model_name not in ('res.partner', 'res.users'):
                continue
            # Ensure the current user has access to write to this model (otherwise they cannot add attachments)
            try:
                if not self.env[model_name].check_access_rights('write', raise_exception=False):
                    continue
            except Exception:
                continue
            allowed_models.append(model_name)
        return allowed_models

    def action_attach(self):
        """Do attach the files to the corresponding records"""
        self.ensure_one()
        if not self.model_name:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Please select a valid model.'),
                    'type': 'danger',
                    'sticky': False,
                }
            }
        record = self.env[self.model_name].browse(self.res_id)
        if not record.exists():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Selected record does not exist.'),
                    'type': 'danger',
                    'sticky': False,
                }
            }
        # Convert/generate data based on the chosen attachment_type
        base64_data = self.sketch_data
        file_ext = '.png'
        mimetype = 'image/png'
        if self.attachment_type == 'pdf':
            base64_data = self._generate_pdf(self.sketch_data)
            file_ext = '.pdf'
            mimetype = 'application/pdf'
        elif self.attachment_type == 'excel':
            base64_data = self._generate_excel(self.sketch_data)
            file_ext = '.xlsx'
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif self.attachment_type == 'word':
            base64_data = self._generate_word(self.sketch_data)
            file_ext = '.doc'
            mimetype = 'application/msword'
        file_name = f"Sketch_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        self.env['ir.attachment'].create({
            'name': file_name,
            'res_model': self.model_name,
            'res_id': self.res_id,
            'datas': base64_data,
            'type': 'binary',
            'mimetype': mimetype,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Sketch attached successfully to %s') % record.display_name,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    @api.model
    def convert_sketch_format(self, base64_png, file_type):
        """Setting up the appropriate sketch format to be converted to an attachment"""
        file_ext = '.png'
        mimetype = 'image/png'
        base64_data = base64_png
        # Create dummy instance to access dynamic file generators
        dummy = self.env['excalidraw.attach.wizard']
        if file_type == 'pdf':
            base64_data = dummy._generate_pdf(base64_png)
            file_ext = '.pdf'
            mimetype = 'application/pdf'
        elif file_type == 'excel':
            base64_data = dummy._generate_excel(base64_png)
            file_ext = '.xlsx'
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif file_type == 'word':
            base64_data = dummy._generate_word(base64_png)
            file_ext = '.doc'
            mimetype = 'application/msword'
        file_name = f"Sketch_{fields.Datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        # If bytes are returned, decode to string for JSON serialization
        if isinstance(base64_data, bytes):
            base64_data = base64_data.decode('utf-8')
        return {
            'data': base64_data,
            'filename': file_name,
            'mimetype': mimetype
        }

    def _generate_pdf(self, base64_png):
        """Setting up the PDF as an attachment"""
        from PIL import Image as PILImage
        import io
        import base64
        # Ensure base64_png is bytes for b64decode
        if isinstance(base64_png, str):
            base64_png = base64_png.encode('utf-8')
        img_data = base64.b64decode(base64_png)
        img = PILImage.open(io.BytesIO(img_data))
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        pdf_buffer = io.BytesIO()
        img.save(pdf_buffer, format='PDF')
        return base64.b64encode(pdf_buffer.getvalue())

    def _generate_excel(self, base64_png):
        """Setting up the Excel as an attachment"""
        import openpyxl
        from openpyxl.drawing.image import Image as OpenpyxlImage
        import io
        import base64
        # Ensure base64_png is bytes for b64decode
        if isinstance(base64_png, str):
            base64_png = base64_png.encode('utf-8')
        img_data = base64.b64decode(base64_png)
        img_file = io.BytesIO(img_data)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sketch"
        img = OpenpyxlImage(img_file)
        ws.add_image(img, 'A1')
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        return base64.b64encode(excel_buffer.getvalue())

    def _generate_word(self, base64_png):
        """Setting up the word document as an attachment"""
        import base64
        # Ensure base64_png is a string representation for HTML embedding
        if isinstance(base64_png, bytes):
            base64_png = base64_png.decode('utf-8')
        # Generate an HTML-compatible .doc file wrapping the base64 image
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                <title>Sketch Attachment</title>
            </head>
            <body>
                <h2>Sketch Drawing</h2>
                <img src="data:image/png;base64,{base64_png}" alt="Sketch" style="max-width: 100%;" />
            </body>
        </html>
        """
        return base64.b64encode(html_content.encode('utf-8'))
