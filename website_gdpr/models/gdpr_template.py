# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class GDPRTemplate(models.Model):
    """
    The GDPRTemplate class included fields and methode to archive.
        Methods:
            action_archive_template(self):
                To archive the record.
    """
    _name = "gdpr.template"
    _description = "GDPR Template"

    name = fields.Char(string="Title", required=True,
                       help="Providing the name of the template")
    description = fields.Html(string="Short Description", required=True,
                              help="Providing the description for the template")
    active = fields.Boolean(default=True)
    allow_messages = fields.Boolean(string="Allow Gdpr Message", default=True,
                                    help="By enabling this an email will send "
                                         "to the partner while confirming the "
                                         "gdpr request")
    field_ids = fields.Many2many('ir.model.fields',
                                 domain="[('model', '=', 'res.partner')]",
                                 string="Data Fields",
                                 required=True,
                                 help="select the fields to"
                                      " visible to the customer")

    def action_archive_template(self):
        """
        Summary:
            To archive the record
        """
        self.active = False
