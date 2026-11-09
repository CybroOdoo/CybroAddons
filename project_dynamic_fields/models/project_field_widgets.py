# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
"""Project field widgets model."""
from odoo import fields, models


class ProjectFieldWidgets(models.Model):
    """We can't filter a selection field dynamically so when we select a field
    its widgets also need to change according to the selected field type, we
    can't do it by a 'selection' field, need a 'Many2one' field."""
    # pylint: disable=too-few-public-methods
    _name = 'project.field.widgets'
    _rec_name = 'description'
    _description = 'Project Field Widgets'

    name = fields.Char(help="Name")
    description = fields.Char(help="Description")
