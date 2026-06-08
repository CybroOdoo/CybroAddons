# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged
from odoo.fields import Command


@tagged('post_install', '-at_install')
class TestWebsiteRestrictCountryController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_us = cls._get_country('US', 'United States')
        cls.country_ca = cls._get_country('CA', 'Canada')
        cls.website = cls.env['website'].get_current_website()
        cls.website.write({
            'country_ids': [(6, 0, (cls.country_us | cls.country_ca).ids)],
            'default_country_id': cls.country_us.id,
        })
        cls.test_user = cls.env['res.users'].create({
            'name': 'Website Restrict Country Test User',
            'login': 'website_restrict_country_test_user',
            'password': 'website_restrict_country_test_user',
            'groups_id': [
                Command.link(cls.env.ref('base.group_user').id),
                Command.link(cls.env.ref('website.group_website_designer').id),
            ],
        })

    @classmethod
    def _get_country(cls, code, name):
        country = cls.env['res.country'].search([('code', '=', code)], limit=1)
        if not country:
            country = cls.env['res.country'].create({
                'name': name,
                'code': code,
            })
        return country

    def test_website_countries_updates_default_country_and_renders_selection(self):
        self.authenticate(self.test_user.login, 'website_restrict_country_test_user')

        response = self.make_jsonrpc_request(
            '/website/countries',
            {'country_id': self.country_ca.id},
        )

        self.assertIn(self.country_ca.name, response)
        self.assertIn(self.country_us.name, response)
        self.website.invalidate_recordset(['default_country_id'])
        self.assertEqual(self.website.default_country_id, self.country_ca)
