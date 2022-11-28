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
from odoo import fields, models, api


class RecentApps(models.Model):
    _name = 'recent.apps'
    _description = 'Recent Apps'

    name = fields.Char(compute='_compute_icon', store=True)
    app_id = fields.Integer()
    icon = fields.Binary(compute='_compute_icon', store=True)
    user_id = fields.Many2one('res.users')

    @api.depends('app_id')
    def _compute_icon(self):
        menu_ui = self.env['ir.ui.menu']
        for rec in self:
            app = menu_ui.browse(rec.app_id)
            rec.icon = app._compute_web_icon_data(app.web_icon)
            rec.name = app.name
