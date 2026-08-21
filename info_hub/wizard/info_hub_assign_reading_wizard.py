# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models

class InformationAssignReadingWizard(models.TransientModel):
    _name = 'info.hub.assign.reading.wizard'
    _description = 'Assign Article Reading'

    article_id = fields.Many2one(
        comodel_name='info.hub.article',
        string='Article',
        required=True,
        readonly=True,
        help='The article to assign reading obligations for.',
    )
    user_ids = fields.Many2many(
        comodel_name='res.users',
        string='Users to Assign',
        required=True,
        domain=[('share', '=', False)],
        help='Select users who must read and acknowledge this article.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super(InformationAssignReadingWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id') or self.env.context.get('default_article_id')
        if active_id:
            if 'article_id' in fields_list and not res.get('article_id'):
                res['article_id'] = active_id
            if 'user_ids' in fields_list:
                existing_readings = self.env['info.hub.article.reading'].search([
                    ('article_id', '=', active_id)
                ])
                res['user_ids'] = [(6, 0, existing_readings.mapped('user_id').ids)]
        return res

    def action_assign(self):
        self.ensure_one()
        existing_readings = self.env['info.hub.article.reading'].search([
            ('article_id', '=', self.article_id.id)
        ])
        existing_user_ids = set(existing_readings.mapped('user_id.id'))
        selected_user_ids = set(self.user_ids.ids)

        users_to_add = selected_user_ids - existing_user_ids
        users_to_remove = existing_user_ids - selected_user_ids

        # 1. Reset already assigned users who finished reading back to pending
        for reading in existing_readings:
            if reading.user_id.id in selected_user_ids:
                if reading.state == 'read':
                    reading.write({
                        'state': 'pending',
                        'read_date': False,
                    })

        # 2. Add new users
        readings_to_create = []
        for user_id in users_to_add:
            readings_to_create.append({
                'article_id': self.article_id.id,
                'user_id': user_id,
                'state': 'pending',
            })
        if readings_to_create:
            self.env['info.hub.article.reading'].create(readings_to_create)

        # 3. Remove unselected users
        readings_to_remove = existing_readings.filtered(lambda r: r.user_id.id in users_to_remove)
        if readings_to_remove:
            readings_to_remove.unlink()

        # 4. Grant read access to users who don't have access yet
        for user in self.user_ids:
            if self.article_id._get_user_permission(user) == 'none':
                self.article_id.invite_members([user.partner_id.id], 'read')

        return {'type': 'ir.actions.act_window_close'}
