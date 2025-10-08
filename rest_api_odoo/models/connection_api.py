# -*- coding:utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import api, fields, models
from odoo.exceptions import AccessError


class ConnectionApi(models.Model):
    """This class is used to create an api model in which we can create
    records with models and fields, and also we can specify methods."""
    _name = 'connection.api'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model', string="Model",
                               domain="[('transient', '=', False)]",
                               help="Select model which can be accessed by "
                                    "REST api requests.")
    is_get = fields.Boolean(string='GET',
                            help="Select this to enable GET method "
                                 "while sending requests.")
    is_post = fields.Boolean(string='POST',
                             help="Select this to enable POST method"
                                  "while sending requests.")
    is_put = fields.Boolean(string='PUT',
                            help="Select this to enable PUT method "
                                 "while sending requests.")
    is_delete = fields.Boolean(string='DELETE',
                               help="Select this to enable DELETE method "
                                    "while sending requests.")

    @api.onchange('model_id')
    def _onchange_model_id(self):
        for record in self:
            if record.model_id:
                model_name = record.model_id.model
                print(model_name)
                # Check permissions
                try:
                    can_read = self.env[model_name].check_access_rights(
                        'read', raise_exception=False)
                    can_write = self.env[model_name].check_access_rights(
                        'write', raise_exception=False)
                    print(can_write,can_read)
                    # record.can_create = self.env[
                    #     model_name].check_access_rights('create',
                    #                                     raise_exception=False)
                    # record.can_unlink = self.env[
                    #     model_name].check_access_rights('unlink',
                    #                                     raise_exception=False)
                except AccessError:
                    can_read = False
                    can_write = False
                    can_create = False
                    can_unlink = False
