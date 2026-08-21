# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models

class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def _can_bypass_rights_on_media_dialog(self, **attachment_data):
        res = super()._can_bypass_rights_on_media_dialog(**attachment_data)
        if res:
            return True

        # Allow portal users editing a shared article to upload files/images.
        res_model = attachment_data.get('res_model')
        res_id = attachment_data.get('res_id')
        if res_model == 'info.hub.article' and res_id:
            user = self.env.user
            article = self.env['info.hub.article'].sudo().browse(int(res_id))
            if article.exists() and article._get_user_permission(user) == 'edit':
                return True
        return False
