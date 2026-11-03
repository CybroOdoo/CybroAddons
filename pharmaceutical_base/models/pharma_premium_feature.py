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
import os

import odoo.addons
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.modules.module import MANIFEST_NAMES, MODULE_NAME_RE


class PharmaPremiumFeature(models.Model):
    """A premium add-on the free modules can point to.

    Each premium feature is its own module, sold on the Odoo Apps store.
    Installing the module is what switches the feature on; until then the
    free modules show what it would add and link to its Apps page. This
    model only catalogues the add-ons — it holds no licensing state.
    """
    _name = 'pharma.premium.feature'
    _description = 'Premium Add-on'
    _order = 'sequence, name'

    name = fields.Char(
        required=True,
        translate=True,
        help='Specifies the name of the premium feature.',
    )
    code = fields.Char(
        required=True,
        readonly=True,
        help='Technical key the free modules refer to the feature by.',
    )
    sequence = fields.Integer(
        default=10,
        help='Specifies the display order of the feature.',
    )
    module_name = fields.Char(
        string='Add-on Module',
        required=True,
        readonly=True,
        help='Technical name of the module that carries the feature.',
    )
    summary = fields.Char(
        translate=True,
        help='One-line description shown in Settings.',
    )
    description = fields.Html(
        translate=True,
        sanitize_attributes=False,
        help='What the feature does, shown when the feature is opened.',
    )
    purchase_url = fields.Char(
        string='Odoo Apps Page',
        help='Page of the add-on on the Odoo Apps store, where it is '
             'purchased.',
    )
    module_state = fields.Selection(
        selection=[
            ('installed', 'Installed'),
            ('available', 'Available to Install'),
            ('not_available', 'Not Purchased'),
        ],
        string='Add-on State',
        compute='_compute_module_state',
        help='"Available to Install" means the module is on this server but '
             'not installed; "Not Purchased" means it is not on this server.',
    )
    is_installed = fields.Boolean(
        string='Installed',
        compute='_compute_module_state',
        help='Specifies whether the add-on module is installed.',
    )

    _code_uniq = models.Constraint(
        'unique(code)',
        'A premium feature code must be unique.',
    )

    def _get_module(self):
        """The ir.module.module record of the add-on, if it is on the server."""
        self.ensure_one()
        return self.env['ir.module.module'].sudo().search(
            [('name', '=', self.module_name)], limit=1)

    def _is_in_addons_path(self):
        """Whether the add-on's module folder is in the addons path now.

        The disk is read on every call: Odoo keeps a module's record after
        its folder is removed, and caches manifests until the server restarts.
        """
        self.ensure_one()
        if not MODULE_NAME_RE.match(self.module_name or ''):
            return False
        return any(
            os.path.isfile(os.path.join(path, self.module_name, manifest))
            for path in odoo.addons.__path__
            for manifest in MANIFEST_NAMES
        )

    def _list_module(self):
        """The add-on's module, listing it first when its folder was added
        to the addons path but Update Apps List was not run."""
        self.ensure_one()
        module = self._get_module()
        if module.state in (False, 'uninstallable') and self._is_in_addons_path():
            self.env['ir.module.module'].sudo().update_list()
            module = self._get_module()
        return module

    @api.depends('module_name')
    def _compute_module_state(self):
        """Read the add-on's state from the module list, counting it as
        available only while its folder is in the addons path."""
        for rec in self:
            module = rec._get_module()
            if module.state == 'installed':
                rec.module_state = 'installed'
            elif module.state != 'to remove' and rec._is_in_addons_path():
                rec.module_state = 'available'
            else:
                rec.module_state = 'not_available'
            rec.is_installed = rec.module_state == 'installed'

    @api.model
    def _pharma_feature_installed(self, code):
        """Whether the add-on of the feature ``code`` is installed."""
        feature = self.sudo().search([('code', '=', code)], limit=1)
        return bool(feature) and feature.is_installed

    @api.model
    def _pharma_feature_on_server(self, code):
        """Whether the module of the feature ``code`` is on this server."""
        feature = self.sudo().search([('code', '=', code)], limit=1)
        return bool(feature) and feature.module_state != 'not_available'

    def action_open_dialog(self):
        """Open the feature's description as a dialog."""
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.premium.feature',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref(
                'pharmaceutical_base.pharma_premium_feature_view_form').id,
                'form')],
            'target': 'new',
        }

    @api.model
    def action_open_dialog_by_code(self, code):
        """Open the dialog of the feature ``code``, for callers holding no record."""
        feature = self.search([('code', '=', code)], limit=1)
        if not feature:
            raise UserError(self.env._('No premium feature is registered under %s.', code))
        return feature.action_open_dialog()

    def action_open_purchase(self):
        """Send the customer to the add-on's page on the Odoo Apps store."""
        self.ensure_one()
        if not self.purchase_url:
            raise UserError(self.env._('No Apps page is set for %s.', self.name))
        return {
            'type': 'ir.actions.act_url',
            'url': self.purchase_url,
            'target': 'new',
        }

    def action_install(self):
        """Install the add-on once its module is on the server."""
        self.ensure_one()
        if not self.env.user.has_group('base.group_system'):
            raise UserError(self.env._('Only an administrator can install %s.', self.name))
        if self.module_state != 'available':
            raise UserError(self.env._('The %(name)s module (%(module)s) is not on this server. '
                'Purchase it on the Odoo Apps store and add it to the addons '
                'path first.', name=self.name, module=self.module_name))
        return self._list_module().button_immediate_install()
