# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Fansa Jabeen A  (odoo@cybrosys.com)
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
from odoo import fields, models


class LabTestContentType(models.Model):
    """
       Model for managing test content types
    """
    _name = 'lab.test.content.type'
    _rec_name = 'content_type_name'
    _description = "Content"

    content_type_name = fields.Char(string="Name", required=True,
                                    help="Content type name")
    content_type_code = fields.Char(string="Code", help="Content type code")
    parent_test_id = fields.Many2one('lab.test',
                                  string="Test Category",
                                  help="Category of test")
