# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class WmDriverChangeHistory(models.Model):
    """Audit log capturing mid-route driver reassignment events with reason and timestamp."""
    _name = 'wm.driver.change.history'
    _description = 'Driver Change History'
    _order = 'create_date desc'

    route_id = fields.Many2one('wm.route', string='Route', required=True, ondelete='cascade')
    old_driver_id = fields.Many2one('res.partner', string='Old Driver')
    new_driver_id = fields.Many2one('res.partner', string='New Driver', required=True)
    reason = fields.Text(string='Reason for Change', required=True)
    changed_by_id = fields.Many2one('res.users', string='Changed By', default=lambda self: self.env.user)
    date_changed = fields.Datetime(string='Date Changed', default=fields.Datetime.now)
