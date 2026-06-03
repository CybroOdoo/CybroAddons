# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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

from odoo import models, fields


class WorkshopTeam(models.Model):
    _name = 'workshop.team'
    _description = 'Workshop Team'

    name = fields.Char('Team Name', help='name of the workshop team',
                       required=True)
    active = fields.Boolean('Active', default=True, help='Active')


class QualityCheckList(models.Model):
    _name = 'quality.check.list'
    _description = 'Quality Check List'

    name = fields.Char(help='Name for the Quality Check List', required=True)
    description = fields.Text('Description', help='Description')
