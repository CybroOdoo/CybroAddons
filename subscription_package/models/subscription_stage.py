# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields


class SubscriptionPackageStage(models.Model):
    _name = "subscription.package.stage"
    _description = "Subscription Package Stages"
    _rec_name = 'name'

    name = fields.Char(string='Stage Name', required=True)
    sequence = fields.Integer('Sequence', help="Determine the display order",
                              index=True)
    condition = fields.Text(string='Conditions')
    fold = fields.Boolean(string='Folded in Kanban',
                          help="This stage is folded in the kanban view "
                               "when there are no records in that stage "
                               "to display.")
    category = fields.Selection([('draft', 'Draft'),
                                 ('progress', 'In Progress'),
                                 ('closed', 'Closed')],
                                readonly=False, default='draft')
