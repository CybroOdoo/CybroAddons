# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil M (odoo@cybrosys.com)
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
from random import randint
from odoo import fields, models


class AttachmentTag(models.Model):
    """Attachment tag model."""
    _name = "ir.attachment.tag"
    _description = "Attachment Tag"

    def _get_default_color(self):
        """To get default color for tags."""
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True, translate=True,
                       help='Name of tags.')
    color = fields.Integer(string='Color', default=_get_default_color,
                           help="Tag color.")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),]
