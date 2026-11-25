# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import AccessDenied
from odoo.http import request


class ResUsers(models.Model):
    """Inherited the res_users model for adding the fields for menu lock setup."""
    _inherit = 'res.users'

    password_lock = fields.Selection(
        [('single_password', 'Single Password Lock'),
         ('multi_password', 'Multi Password Lock')],
        groups='base.group_system', string='Menu Lock Password Type',
        help='Type of Menu Lock Password')
    login_password = fields.Char(
        string='Menu Lock Password', groups='base.group_system',
        compute='_compute_login_password', inverse='_set_login_password',
        copy=False, help='Enter a new password to replace the current lock password.')
    menu_lock_hash = fields.Char(groups='base.group_system', copy=False)
    menus_to_lock_ids = fields.Many2many(
        'ir.ui.menu',
        groups="base.group_system", string="Menus to lock",
        domain="[('parent_id','=',False)]",
        help='Select the menus to lock')
    multi_lock_ids = fields.One2many(
        'menu.password',
        'password_id',
        groups='base.group_system', string='Multi menus to lock',
        help='Multi lock menus and password')
    models_to_lock_ids = fields.Many2many('ir.model',
                                          groups='base.group_system', string='Models to lock')

    def _compute_login_password(self):
        self.login_password = False

    def _set_login_password(self):
        for user in self:
            value = user.login_password
            user.menu_lock_hash = self._crypt_context().hash(value) if value else False

        self.invalidate_recordset(['login_password'])

    @api.model
    def _menu_lock_hashes(self, menu_id):
        """Resolve the current user's policy from the same menu tree as the navbar."""
        if not self.env.user.has_group('base.group_user') or type(menu_id) is not int:
            raise AccessDenied()
        menu = self.env['ir.ui.menu'].load_web_menus(request.session.debug if request else False).get(menu_id)
        if not menu:
            raise AccessDenied()
        user = self.env.user.sudo()
        hashes = []
        if user.password_lock == 'single_password':
            if menu['appID'] in user.menus_to_lock_ids.ids:
                hashes.append(user.menu_lock_hash)
        elif user.password_lock == 'multi_password':
            lines = user.multi_lock_ids.filtered(lambda line: line.menus_id.id == menu['appID'])
            hashes.extend(lines.mapped('menu_lock_hash'))
        if user.models_to_lock_ids and menu['actionModel'] == 'ir.actions.act_window':
            action = self.env['ir.actions.act_window'].sudo().browse(menu['actionID'])
            if action.res_model in user.models_to_lock_ids.mapped('model'):
                hashes.append(user.menu_lock_hash)
        return hashes

    @api.model
    def menu_lock_required(self, menu_id):
        return bool(self._menu_lock_hashes(menu_id))

    @api.model
    def verify_menu_lock(self, menu_id, password):
        hashes = self._menu_lock_hashes(menu_id)
        if not hashes:
            return True
        if not isinstance(password, str) or not password:
            return False
        try:
            with self._assert_can_auth(user=self.env.uid):
                for encoded in hashes:
                    if encoded and self._crypt_context().verify(password, encoded):
                        return True
                raise AccessDenied()
        except AccessDenied:
            return False
