# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from lxml import etree

from odoo import api, models


class Board(models.AbstractModel):
    _inherit = 'board.board'

    @api.model
    def _sanitize_openacademy_dashboard_arch(self, arch):
        root = etree.fromstring(arch)
        for action in root.xpath('.//board/column/action'):
            if action.get('context') in (None, '', 'null'):
                action.set('context', '{}')
            if action.get('domain') in (None, '', 'null'):
                action.set('domain', '[]')
        return etree.tostring(root, encoding='unicode')

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type != 'form' or not view_id:
            return res

        dashboard_view = self.env.ref(
            'open_academy.board_session_form', raise_if_not_found=False
        )
        if not dashboard_view or dashboard_view.id != view_id:
            return res

        res['arch'] = self._sanitize_openacademy_dashboard_arch(res['arch'])
        if res.get('custom_view_id'):
            return res

        custom_view = self.env['ir.ui.view.custom'].sudo().create({
            'user_id': self.env.uid,
            'ref_id': view_id,
            'arch': res['arch'],
        })
        res['custom_view_id'] = custom_view.id
        return res
