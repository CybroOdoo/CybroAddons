# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class DocumentTag(models.Model):
    """ Model used to store tags """
    _name = "document.tag"
    _description = "Document Tag"

    name = fields.Char(string="Name", required=True)

    @api.constrains('name')
    def _check_unique_name(self):
        """ Python constraint to ensure tag name uniqueness as a fallback
        for the SQL constraint and to provide descriptive errors. """
        for record in self:
            if record.name:
                normalized_name = record.name.strip()
                duplicate = self.search([
                    ('name', '=ilike', normalized_name),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_("Tag name '%s' already exists!") % record.name)
