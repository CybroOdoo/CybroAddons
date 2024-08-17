# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Hafeesul Ali(<https://www.cybrosys.com>)
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
from odoo import api, models


class IrAttachment(models.Model):
    """
    This model extends the functionality of 'ir.attachment' in Odoo.
    """
    _inherit = 'ir.attachment'

    @api.model
    def get_fields(self, value):
        """
        Retrieve specified fields from attachments identified by the given list of IDs.
        """
        data_list = []
        for values in value:
            attach = self.env['ir.attachment'].browse(values)
            data_dict = {
                'attachment': attach.id,
                'datas': attach.datas,
                'mimetype': attach.mimetype,
                'name': attach.name
            }
            data_list.append(data_dict)
        return data_list
