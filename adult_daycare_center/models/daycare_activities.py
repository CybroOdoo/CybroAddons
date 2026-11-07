# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
##########################################################################
from odoo import fields, models


class DaycareActivitiesView(models.Model):
    """Manage daycare activities and their assigned responsibilities."""
    _name = 'daycare.activities'
    _description = 'Day Care Activities'

    activity_id = fields.Many2one('activity.type', string='Name',
                                  help="Activity Name", required=True)
    product_id = fields.Many2one('product.template', required=True, help="Adult activity",
                                 domain=[('is_adult_activity', '=', True)])
    notes = fields.Char(help="Extra information")
    time_in = fields.Float(help="Time in for the activity")
    time_out = fields.Float(help="Time out for the activity")
    responsible_id = fields.Many2one('res.users', string='Responsible By',
                                  help="Responsible by the activity")
    res_partner_id = fields.Many2one('res.partner', string='Partner',
                                     help="Responsible partner for the "
                                          "activity")
