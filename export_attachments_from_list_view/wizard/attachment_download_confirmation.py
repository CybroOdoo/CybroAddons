# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
from odoo import models
from odoo.exceptions import ValidationError


class AttachmentDownloadConfirmation(models.TransientModel):
    """It displays a confirmation user input popup regardless of the attachment.
       download or not."""
    _name = 'attachment.download.confirmation'
    _description = 'Confirmation Popup'

    def action_download_attachment(self):
        """Method to Download the attachment"""
        record_ids = self.env.context.get('active_ids', [])
        record_model = self.env.context.get('active_model')
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', record_model),
            ('res_id', '=', record_ids)])
        if not attachments:
            raise ValidationError("No attachments found in the selected "
                                  "records.")
        else:
            url = '/web/binary/download_document?tab_id=%s' % attachments.ids
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
