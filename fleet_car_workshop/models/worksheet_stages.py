# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class WorksheetStages(models.Model):
    """Model for work sheet stages """
    _name = 'worksheet.stages'
    _description = 'worksheet Stage of Worksheet'
    _order = 'sequence'

    def _default_vehicle_ids(self):
        """Get the default vehicle id """
        default_vehicle_id = self.env.context.get('default_vehicle_id')
        return [default_vehicle_id] if default_vehicle_id else None

    name = fields.Char(string='Stage Name', required=True,
                       help='Name of the stage')
    description = fields.Text(string='Description', translate=True,
                              help='Description of the stage')
    sequence = fields.Integer(string='Sequence',help='Sequence of the stage')
    vehicle_ids = fields.Many2many('vehicle.details',
                                   'worksheet_type_rel', 'type_id',
                                   'vehicle_id', string='Vehicles',
                                   default=_default_vehicle_ids,
                                   help='Vehicle details of the stage')
    is_fold = fields.Boolean(string='Folded in Tasks Pipeline',
                          help='This stage is folded in the kanban view when '
                               'there are no records in that stage to display.')
