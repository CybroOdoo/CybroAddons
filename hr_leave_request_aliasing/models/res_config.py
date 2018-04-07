# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import api, fields, models


class HrLeaveConfigSettings(models.TransientModel):
    _name = 'hr.leave.config.settings'
    _inherit = 'res.config.settings'

    alias_prefix = fields.Char(string='Default Alias Name for Leave', help='Default Alias Name for Leave')
    alias_domain = fields.Char(string='Alias Domain', help='Default Alias Domain for Leave',
                               default=lambda self: self.env["ir.config_parameter"].get_param("mail.catchall.domain"))

    @api.model
    def get_default_alias_prefix(self, fields):
        alias_name = self.env.ref('hr_leave_request_aliasing.mail_alias_leave').alias_name
        return {'alias_prefix': alias_name}

    @api.multi
    def set_default_alias_prefix(self):
        for record in self:
            self.env.ref('hr_leave_request_aliasing.mail_alias_leave').write({'alias_name': record.alias_prefix})

