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
from odoo.tests import Form, TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_base')
class TestBaseLowFixes(TransactionCase):
    """Regression tests for the wm_base low-severity fixes."""

    # ---- V-22 ---------------------------------------------------------------
    def test_wizard_signer_role_is_saved(self):
        """The template's roles reach the wizard lines although shown read-only."""
        role = self.env['wm.signature.role'].create({'name': 'Low Role'})
        template = self.env['wm.signature.template'].create({
            'name': 'Low Template',
            'role_ids': [(6, 0, role.ids)],
        })
        partner = self.env['res.partner'].create({'name': 'Low Signer', 'email': 'low.signer@example.com'})
        wizard_form = Form(self.env['wm.signature.request.wizard'].with_context(
            default_res_model='res.partner', default_res_id=partner.id))
        wizard_form.template_id = template
        with wizard_form.signer_ids.edit(0) as line:
            line.partner_id = partner
            line.email = partner.email
        wizard = wizard_form.save()
        self.assertEqual(wizard.signer_ids.role_id, role)
        self.assertEqual(wizard.signer_ids.partner_id, partner)

    # ---- V-23 ---------------------------------------------------------------
    def test_reference_selection_only_installed_models(self):
        """Only installed models are offered as signature request targets."""
        selection = self.env['wm.signature.request']._selection_target_model()
        models = [model for model, _label in selection]
        self.assertNotIn('partner.contract', models)
        for model in models:
            self.assertIn(model, self.env)
        # The field's selection resolves without KeyError
        self.assertEqual(
            [m for m, _l in self.env['wm.signature.request']._fields['reference_doc']._description_selection(self.env)],
            models)

    # ---- V-24 ---------------------------------------------------------------
    def test_menus_restricted_to_wm_roles(self):
        """Internal users without a WM role do not see the WM app menus."""
        Menu = self.env['ir.ui.menu']
        root = self.env.ref('wm_base.menu_wm_root')
        templates = self.env.ref('wm_base.menu_wm_signature_template')
        roles = self.env.ref('wm_base.menu_wm_signature_role')

        plain = new_test_user(self.env, login='low_plain_user', groups='base.group_user')
        driver = new_test_user(self.env, login='low_driver', groups='base.group_user,wm_base.group_wm_driver')
        sign_mgr = new_test_user(self.env, login='low_sign_mgr', groups='base.group_user,wm_base.group_signature_manager')

        plain_visible = Menu.with_user(plain)._visible_menu_ids()
        self.assertNotIn(root.id, plain_visible)

        driver_visible = Menu.with_user(driver)._visible_menu_ids()
        self.assertIn(root.id, driver_visible)
        self.assertNotIn(templates.id, driver_visible)
        self.assertNotIn(roles.id, driver_visible)

        mgr_visible = Menu.with_user(sign_mgr)._visible_menu_ids()
        self.assertIn(templates.id, mgr_visible)
        self.assertIn(roles.id, mgr_visible)
