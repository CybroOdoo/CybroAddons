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

from odoo import models, fields, api


class SubscriptionCloseWizard(models.TransientModel):
    _name = 'subscription.close.wizard'
    _description = 'Subscription Close Wizard'

    close_reason = fields.Many2one('subscription.package.stop', string='Close Reason')
    closed_by = fields.Many2one('res.users', string='Closed By', default=lambda self: self.env.user)
    close_date = fields.Date(string='Closed On', default=lambda self: fields.Date.today())

    def button_submit(self):
        self.ensure_one()
        this_sub_id = self.env.context.get('active_id')
        sub = self.env['subscription.package'].search([('id', '=', this_sub_id)])
        sub.is_closed = True
        sub.close_reason = self.close_reason
        sub.closed_by = self.closed_by
        sub.close_date = self.close_date
        stage = (self.env['subscription.package.stage'].search([
                    ('category', '=', 'closed')]).id)
        values = {'stage_id': stage, 'to_renew': False}
        sub.write(values)
