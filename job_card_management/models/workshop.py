# -*- coding: utf-8 -*-
###################################################################################
#    Job Card Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Manasa T P (<https://www.cybrosys.com>)
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

from odoo import models, fields


class WorkshopTeam(models.Model):
    _name = 'workshop.team'
    _description = 'Workshop Team'

    name = fields.Char(
        string='Team Name',
        required=True,
        help='The name of the workshop team.'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Indicates whether the workshop team is active and available for assignment.'
    )


class QualityCheckList(models.Model):
    _name = 'quality.check.list'
    _description = 'Quality Check List'

    name = fields.Char(
        string='Checklist Name',
        required=True,
        help='The name or title of the quality checklist.'
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of the quality checklist and its purpose.'
    )
