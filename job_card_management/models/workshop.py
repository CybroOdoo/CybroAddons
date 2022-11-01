# -*- coding: utf-8 -*-
###################################################################################
#    Job Card
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
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

    name = fields.Char('Team Name', help='name of the workshop team',
                       required=True)
    active = fields.Boolean('Active', default=True)


class QualityCheckList(models.Model):
    _name = 'quality.check.list'
    _description = 'Quality Check List'

    name = fields.Char(help='Name for the Quality Check List', required=True)
    description = fields.Text('Description')
