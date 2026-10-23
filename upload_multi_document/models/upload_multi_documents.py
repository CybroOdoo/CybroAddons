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
import base64
import binascii

from odoo import api, models
from odoo.exceptions import UserError


class UploadMultiDocuments(models.AbstractModel):
    """ This class handles the creation of attachments for multiple
    documents uploaded at once."""
    _name = "upload.multi.documents"
    _description = "Upload Multiple Documents"

    @api.model
    def document_file_create(self, value, name, selected_ids, model):
        """Attach the uploaded file to each selected record.

        :param str value: file content, either raw base64 or a data URL
            (``data:<mime>;base64,<data>``)
        :param str name: file name of the attachment
        :param list selected_ids: ids of the records to attach the file to
        :param str model: technical name of the records' model
        :return: True when attachments were created, False when no record
            was selected
        :raises UserError: on invalid input
        :raises AccessError: if the user cannot write on the records
        """
        if not selected_ids:
            return False
        if not isinstance(model, str) or model not in self.env:
            raise UserError(self.env._("Unknown model: %(model)s", model=model))
        if (
            not isinstance(selected_ids, (list, tuple))
            or not all(isinstance(rec_id, int) and not isinstance(rec_id, bool)
                       for rec_id in selected_ids)
        ):
            raise UserError(self.env._("The selected records are invalid."))
        if not isinstance(name, str) or not name:
            raise UserError(self.env._("The file name is required."))
        if not value or not isinstance(value, str):
            raise UserError(self.env._("The uploaded file is empty."))

        records = self.env[model].browse(list(dict.fromkeys(selected_ids)))
        if len(records.exists()) != len(records):
            raise UserError(self.env._("Some of the selected records no longer exist."))
        records.check_access('write')

        data = value.split(',', 1)[1] if ',' in value else value
        try:
            raw = base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError) as error:
            raise UserError(self.env._("The uploaded file is not valid base64 data.")) from error
        if not raw:
            raise UserError(self.env._("The uploaded file is empty."))

        self.env['ir.attachment'].create([{
            'name': name,
            'raw': raw,
            'res_model': model,
            'res_id': rec_id,
        } for rec_id in records.ids])
        return True
