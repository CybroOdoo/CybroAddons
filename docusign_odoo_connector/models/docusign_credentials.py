# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil @ cybrosys,(odoo@cybrosys.com)
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
###############################################################################
from . import docusign
from odoo import models, fields
from odoo.exceptions import UserError


class DocusignCredentials(models.Model):
    """ To set up the Docusign account credentials for integrating with odoo"""
    _name = 'docusign.credentials'
    _description = "Docusign Credentials Setup"

    name = fields.Char(string="Name", required=True, help="Name of record")
    integrator_key = fields.Char(string="Docusign Integrator Key",
                                 required=True, help="Docusign Integrator key")
    account_id_data = fields.Char(string='Docusign Account Id', required=True,
                                  help="Docusign user account ID")
    user_id_data = fields.Char(string='Docusign User Id', required=True,
                               help="Docusign user ID")
    private_key_ids = fields.Many2many('ir.attachment',
                                       string='Private Key File',
                                       required=True,
                                       help="Private key attachment")
    company_id = fields.Many2one('res.company', string="Operator",
                                 default=lambda self: self.env.user.company_id,
                                 help="company ID",
                                 context={'user_preference': True})

    def action_test_credentials(self):
        """ Function to test whether the credentials are valid or not"""
        status = docusign.action_login_docusign(self.user_id_data,
                                                self.account_id_data,
                                                self.integrator_key,
                                                self.private_key_ids)
        if status != 200:
            raise UserError("Connection Failed!")
        else:
            raise UserError(" Connection Successful !")
