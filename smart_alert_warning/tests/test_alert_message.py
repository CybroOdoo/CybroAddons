#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from lxml import etree

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smart_alert_warning import uninstall_hook


@tagged('post_install', '-at_install')
class TestAlertMessage(TransactionCase):
    """Test the alert views created from alert.message."""

    @classmethod
    def setUpClass(cls):
        """Create partners to evaluate the filters on."""
        super().setUpClass()
        cls.partner_model = cls.env['ir.model']._get('res.partner')
        cls.partner_view = cls.env.ref('base.view_partner_form')
        cls.country_be = cls.env.ref('base.be')
        # is_company is computed from the VAT number since Odoo 20
        cls.partners = cls.env['res.partner'].create([
            {'name': 'Alpha Corp', 'vat': 'BE0477472701',
             'country_id': cls.country_be.id, 'color': 3},
            {'name': 'beta shop', 'color': 7},
            {'name': 'Gamma', 'vat': 'BE0477472701', 'email': 'g@example.com'},
        ])
        assert cls.partners.mapped('is_company') == [True, False, True]
        # Neither user has the Settings access, unlike the superuser
        cls.alert_admin = new_test_user(
            cls.env, login='alert_admin',
            groups='smart_alert_warning.smart_alert_warning_group_admin')
        cls.alert_user = new_test_user(
            cls.env, login='alert_user',
            groups='smart_alert_warning.smart_alert_warning_group_user')

    def _create_alert(self, **values):
        """Create a draft alert on the partner form view."""
        return self.env['alert.message'].create({
            'name': 'Test Alert',
            'document_type_id': self.partner_model.id,
            'view_id': self.partner_view.id,
            'alert_messages': 'Check this partner',
            'type': 'alert-warning',
            **values,
        })

    def _get_alert_node(self, alert):
        """Return the alert div of the view created by ``alert``."""
        arch = etree.fromstring(alert.new_view_id.arch)
        return arch.find('.//div[@role="alert"]')

    def _client_values(self, partner, field_names):
        """Values of ``partner`` as the web client evaluates them in the
        form view: many2one as ids, unset values as False."""
        values = {}
        for name in field_names:
            value = partner[name]
            if partner._fields[name].type == 'many2one':
                value = value.id
            elif partner._fields[name].type == 'datetime':
                value = fields.Datetime.to_string(value)
            values[name] = value if value or value == 0 else False
        return values

    def assertFilterMatchesSearch(self, domain, field_names):
        """The alert must show exactly on the partners the domain matches."""
        alert = self._create_alert(field_filter=str(domain))
        alert.action_apply()
        invisible = self._get_alert_node(alert).get('invisible')
        matching = self.env['res.partner'].search(
            [('id', 'in', self.partners.ids)] + domain)
        for partner in self.partners:
            hidden = safe_eval(invisible,
                               self._client_values(partner, field_names))
            self.assertEqual(
                not hidden, partner in matching,
                f"{domain} on {partner.name}: invisible={invisible!r}")

    def test_01_initial_state(self):
        """A new alert is a draft without view."""
        alert = self._create_alert()
        self.assertEqual(alert.state, 'draft')
        self.assertFalse(alert.new_view_id)

    def test_02_apply_without_group_and_filter(self):
        """Without group nor filter, the alert shows to everyone."""
        alert = self._create_alert(type='alert-info')
        alert.action_apply()
        self.assertEqual(alert.state, 'done')
        node = self._get_alert_node(alert)
        self.assertEqual(node.get('class'), 'alert alert-info o_smart_alert')
        self.assertEqual(node.text, 'Check this partner')
        self.assertIsNone(node.get('groups'))
        self.assertIsNone(node.get('invisible'))

    def test_03_apply_with_group(self):
        """The alert is restricted to the group with its XML id."""
        group = self.env.ref('base.group_system')
        alert = self._create_alert(group_id=group.id)
        alert.action_apply()
        self.assertEqual(self._get_alert_node(alert).get('groups'),
                         'base.group_system')

    def test_04_apply_with_group_without_xml_id(self):
        """A group created from the interface gets an XML id for the view."""
        group = self.env['res.groups'].create({'name': 'Alert Readers'})
        alert = self._create_alert(group_id=group.id)
        alert.action_apply()
        xml_id = self._get_alert_node(alert).get('groups')
        self.assertTrue(xml_id.startswith('__export__.'), xml_id)
        self.assertEqual(self.env.ref(xml_id), group)

    def test_05_filter_single_conditions(self):
        """Each operator shows the alert on the records it matches."""
        for domain, field_names in [
            ([('is_company', '=', True)], ['is_company']),
            ([('is_company', '!=', True)], ['is_company']),
            ([('color', '>', 3)], ['color']),
            ([('color', '<', 7)], ['color']),
            ([('color', '>=', 7)], ['color']),
            ([('color', '<=', 3)], ['color']),
            ([('color', 'in', [3, 7])], ['color']),
            ([('color', 'not in', [3])], ['color']),
            ([('name', 'ilike', 'BETA')], ['name']),
            ([('name', 'not ilike', 'corp')], ['name']),
            ([('name', 'like', 'Gam')], ['name']),
            ([('email', '!=', False)], ['email']),
            ([('email', '=', False)], ['email']),
            ([('country_id', '=', self.country_be.id)], ['country_id']),
            ([('country_id', 'in', [self.country_be.id])], ['country_id']),
            ([('type', 'ilike', 'CONT')], ['type']),
            ([('create_date', '>', '2000-01-01 00:00:00')], ['create_date']),
            ([('create_date', '<', '2000-01-01 00:00:00')], ['create_date']),
        ]:
            with self.subTest(domain=domain):
                self.assertFilterMatchesSearch(domain, field_names)

    def test_06_filter_combined_conditions(self):
        """Domains with several conditions, | and ! work, not only the first
        condition."""
        for domain, field_names in [
            ([('is_company', '=', True), ('color', '=', 3)],
             ['is_company', 'color']),
            (['|', ('color', '=', 7), ('email', '!=', False)],
             ['color', 'email']),
            (['!', ('name', 'ilike', 'alpha')], ['name']),
            (['&', '|', ('color', '=', 3), ('color', '=', 7),
              ('is_company', '=', False)], ['color', 'is_company']),
        ]:
            with self.subTest(domain=domain):
                self.assertFilterMatchesSearch(domain, field_names)

    def test_07_filter_is_valid_in_the_form_view(self):
        """The combined form view loads with the alert and its condition."""
        alert = self._create_alert(
            field_filter=str([('is_company', '=', True), ('color', '>', 2)]))
        alert.action_apply()
        arch = self.env['res.partner'].get_view(self.partner_view.id)['arch']
        node = etree.fromstring(arch).find(
            './/div[@role="alert"][@class="alert alert-warning o_smart_alert"]')
        self.assertIsNotNone(node)
        self.assertEqual(node.get('invisible'),
                         'not ((is_company == True) and (color > 2))')

    def test_08_message_is_escaped(self):
        """Special characters in the message do not break the view."""
        message = 'Credit <limit> & "overdue" invoices'
        alert = self._create_alert(alert_messages=message)
        alert.action_apply()
        self.assertEqual(self._get_alert_node(alert).text, message)

    def test_09_unsupported_filters(self):
        """Filters the form view cannot evaluate are refused clearly."""
        for domain in [
            [('country_id.code', '=', 'BE')],
            [('category_id', 'in', [1])],
            [('name', '=like', 'A%')],
            # The form view has the id of a many2one, which has no lower()
            [('country_id', 'ilike', 'Bel')],
            [('country_id', 'not ilike', 'Bel')],
            [('country_id', '=', 'Belgium')],
            [('country_id', 'in', ['Belgium'])],
            [('color', 'ilike', '1')],
            [('is_company', 'ilike', 'x')],
            [('name', 'in', 'Alpha')],
        ]:
            with self.subTest(domain=domain):
                alert = self._create_alert(field_filter=str(domain))
                with self.assertRaises(UserError):
                    alert.action_apply()
                self.assertEqual(alert.state, 'draft')
                self.assertFalse(alert.new_view_id)

    def test_10_cancel_and_reset(self):
        """Cancelling removes the view, and the alert can be reset."""
        alert = self._create_alert()
        alert.action_apply()
        view = alert.new_view_id
        alert.action_cancel()
        self.assertEqual(alert.state, 'cancelled')
        self.assertFalse(view.exists())
        self.assertFalse(alert.new_view_id)
        alert.action_reset_draft()
        self.assertEqual(alert.state, 'draft')
        alert.action_apply()
        self.assertEqual(alert.state, 'done')
        self.assertTrue(alert.new_view_id)

    def test_11_unlink_removes_view(self):
        """Deleting an applied alert removes its view."""
        alert = self._create_alert()
        alert.action_apply()
        view = alert.new_view_id
        alert.unlink()
        self.assertFalse(view.exists())

    def test_12_view_without_sheet(self):
        """A form view without sheet is refused with a clear error."""
        view = self.env['ir.ui.view'].create({
            'name': 'res.partner.form.nosheet',
            'model': 'res.partner',
            'type': 'form',
            'arch': '<form><field name="name"/></form>',
        })
        alert = self._create_alert(view_id=view.id)
        with self.assertRaises(UserError):
            alert.action_apply()

    def test_13_malformed_filters(self):
        """Malformed filters are refused, not raised as a server error."""
        for field_filter in [
            '5',
            "'abc'",
            '[(',
            "['&', ('color', '=', 1)]",
            "['|']",
            "[('color', '=')]",
            "[('date', '>=', context_today().strftime('%Y-%m-%d'))]",
        ]:
            with self.subTest(field_filter=field_filter):
                alert = self._create_alert(field_filter=field_filter)
                with self.assertRaises(UserError):
                    alert.action_apply()

    def test_14_filter_on_restricted_field(self):
        """A field missing for some users would break their form view."""
        field = self.env['res.partner']._fields['email']
        self.patch(field, 'groups', 'base.group_system')
        alert = self._create_alert(field_filter="[('email', '!=', False)]")
        with self.assertRaises(UserError):
            alert.action_apply()

    def test_15_alert_admin_without_settings_access(self):
        """An alert admin can do the whole flow without Settings access."""
        env = self.env(user=self.alert_admin)
        self.assertTrue(env['ir.model'].name_search('Contact'))
        self.assertTrue(env['ir.ui.view'].name_search(
            'res.partner.form', [('model', '=', 'res.partner'),
                                 ('type', '=', 'form')]))
        alert = env['alert.message'].create({
            'name': 'Admin Alert',
            'document_type_id': self.partner_model.id,
            'view_id': self.partner_view.id,
            'alert_messages': 'Check this partner',
            'type': 'alert-danger',
            'group_id': self.env['res.groups'].create({'name': 'Readers'}).id,
            'field_filter': "[('color', '>', 2)]",
        })
        alert.action_apply()
        self.assertEqual(alert.state, 'done')
        view = alert.new_view_id
        self.assertTrue(view)
        alert.action_cancel()
        self.assertFalse(view.sudo().exists())
        alert.action_reset_draft()
        alert.action_apply()
        view = alert.new_view_id
        alert.unlink()
        self.assertFalse(view.sudo().exists())

    def test_16_alert_user_is_read_only(self):
        """An alert user can open an alert the way the form does."""
        alert = self._create_alert()
        alert.action_apply()
        result = alert.with_user(self.alert_user).web_read({
            'name': {},
            'document_type_id': {'fields': {'display_name': {}}},
            'view_id': {'fields': {'display_name': {}}},
            'new_view_id': {'fields': {'display_name': {}}},
            'model_name': {},
        })
        self.assertEqual(result[0]['model_name'], 'res.partner')
        with self.assertRaises(AccessError):
            alert.with_user(self.alert_user).write({'name': 'Changed'})

    def test_17_copy_does_not_share_the_view(self):
        """Deleting a copy must leave the banner of the original alert."""
        alert = self._create_alert()
        alert.action_apply()
        copy = alert.copy()
        self.assertEqual(copy.state, 'draft')
        self.assertFalse(copy.new_view_id)
        copy.unlink()
        self.assertTrue(alert.new_view_id.exists())

    def test_18_apply_twice(self):
        """Applying an applied alert must not leave a second view."""
        alert = self._create_alert()
        alert.action_apply()
        view = alert.new_view_id
        alert.action_apply()
        self.assertEqual(alert.new_view_id, view)

    def test_19_several_alerts_on_one_form(self):
        """Each alert keeps its own style and condition."""
        alerts = self._create_alert(
            type='alert-info', field_filter="[('color', '=', 1)]",
        ) | self._create_alert(
            type='alert-danger', field_filter="[('color', '=', 2)]")
        alerts.action_apply()
        arch = etree.fromstring(
            self.env['res.partner'].get_view(self.partner_view.id)['arch'])
        for style, condition in (('info', 'not (color == 1)'),
                                 ('danger', 'not (color == 2)')):
            node = arch.find(f'.//div[@class="alert alert-{style} o_smart_alert"]')
            self.assertEqual(node.get('invisible'), condition)

    def test_20_change_document_type(self):
        """The view and filter of the old document type are cleared."""
        alert = self._create_alert(field_filter="[('color', '=', 1)]")
        alert._onchange_document_type_id()
        self.assertFalse(alert.view_id)
        self.assertEqual(alert.field_filter, '[]')

    def test_21_uninstall_hook_removes_the_banners(self):
        """The alert views must not stay on the forms after uninstalling."""
        alert = self._create_alert()
        alert.action_apply()
        view = alert.new_view_id
        uninstall_hook(self.env)
        self.assertFalse(view.exists())
