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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import psycopg2
from odoo.exceptions import AccessError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestThemeLiveloModels(common.TransactionCase):
    """Test suite for theme_livelo models: property.amenity and product.template extensions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()

        # Load theme templates onto current website
        theme_module = cls.env['ir.module.module'].search([('name', '=', 'theme_livelo')])
        if theme_module:
            theme_module.with_context(load_all_views=True)._theme_load(cls.website)

        cls.Amenity = cls.env['property.amenity']
        cls.ProductTemplate = cls.env['product.template']
        cls.ResUsers = cls.env['res.users']

        # Create test users for access right testing
        cls.user_internal = cls.ResUsers.create({
            'name': 'Internal Test User',
            'login': 'internal_test_user@livelo.test',
            'email': 'internal_test_user@livelo.test',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        cls.user_portal = cls.ResUsers.create({
            'name': 'Portal Test User',
            'login': 'portal_test_user@livelo.test',
            'email': 'portal_test_user@livelo.test',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

        cls.user_public = cls.ResUsers.create({
            'name': 'Public Test User',
            'login': 'public_test_user@livelo.test',
            'email': 'public_test_user@livelo.test',
            'group_ids': [(6, 0, [cls.env.ref('base.group_public').id])],
        })

        # Test amenity
        cls.amenity_pool = cls.Amenity.create({
            'name': 'Olympic Pool',
            'icon': 'fa fa-swimming-pool',
        })
        cls.amenity_garden = cls.Amenity.create({
            'name': 'Private Garden',
            'icon': 'fa fa-tree',
        })

    def test_01_create_amenity(self):
        """Test creating property amenity and verifying field values."""
        amenity = self.Amenity.create({
            'name': 'Rooftop Terrace',
            'icon': 'fa fa-sun-o',
        })
        self.assertEqual(amenity.name, 'Rooftop Terrace')
        self.assertEqual(amenity.icon, 'fa fa-sun-o')

        # Test requirement of name
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.Amenity.create({'icon': 'fa fa-question'})

    def test_02_amenity_access_rights(self):
        """Test CRUD permissions on property.amenity for internal, portal, and public users."""
        # 1. Internal user should have full CRUD rights
        amenity_as_internal = self.Amenity.with_user(self.user_internal).create({
            'name': 'Sauna Room',
            'icon': 'fa fa-hot-tub',
        })
        self.assertTrue(amenity_as_internal.id)
        amenity_as_internal.write({'name': 'Deluxe Sauna Room'})
        self.assertEqual(amenity_as_internal.name, 'Deluxe Sauna Room')
        amenity_id = amenity_as_internal.id
        amenity_as_internal.unlink()
        self.assertFalse(self.Amenity.browse(amenity_id).exists())

        # 2. Portal user can read, but cannot create, write, or delete
        amenity_as_portal = self.amenity_pool.with_user(self.user_portal)
        self.assertEqual(amenity_as_portal.name, 'Olympic Pool')

        with self.assertRaises(AccessError):
            self.Amenity.with_user(self.user_portal).create({'name': 'Portal Amenity'})

        with self.assertRaises(AccessError):
            amenity_as_portal.write({'name': 'Modified Pool'})

        with self.assertRaises(AccessError):
            amenity_as_portal.unlink()

        # 3. Public user can read, but cannot create, write, or delete
        amenity_as_public = self.amenity_pool.with_user(self.user_public)
        self.assertEqual(amenity_as_public.name, 'Olympic Pool')

        with self.assertRaises(AccessError):
            self.Amenity.with_user(self.user_public).create({'name': 'Public Amenity'})

        with self.assertRaises(AccessError):
            amenity_as_public.write({'name': 'Public Modified'})

        with self.assertRaises(AccessError):
            amenity_as_public.unlink()

    def test_03_product_template_property_defaults(self):
        """Test default values on product.template for custom property fields."""
        standard_product = self.ProductTemplate.create({
            'name': 'Standard Desk',
            'list_price': 150.0,
        })
        self.assertFalse(standard_product.is_property)
        self.assertFalse(standard_product.is_featured)
        self.assertEqual(standard_product.listing_type, 'sale')
        self.assertEqual(standard_product.garages, 1)
        self.assertEqual(standard_product.year_built, 2024)
        self.assertFalse(standard_product.property_type)
        self.assertFalse(standard_product.amenity_ids)
        self.assertFalse(standard_product.salesperson_id)

    def test_04_product_template_property_fields(self):
        """Test assigning and updating all property fields on product.template."""
        property_product = self.ProductTemplate.create({
            'name': 'Sunset Modern Villa',
            'list_price': 850000.0,
            'is_property': True,
            'is_featured': True,
            'listing_type': 'sale',
            'property_type': 'villa',
            'location': 'Sunset Boulevard 101, Los Angeles',
            'bed': 4,
            'bath': 3,
            'squarefeet': 3200,
            'garages': 2,
            'year_built': 2022,
            'land_size': 5000,
            'salesperson_id': self.user_internal.id,
            'amenity_ids': [(6, 0, [self.amenity_pool.id, self.amenity_garden.id])],
        })

        self.assertTrue(property_product.is_property)
        self.assertTrue(property_product.is_featured)
        self.assertEqual(property_product.listing_type, 'sale')
        self.assertEqual(property_product.property_type, 'villa')
        self.assertEqual(property_product.location, 'Sunset Boulevard 101, Los Angeles')
        self.assertEqual(property_product.bed, 4)
        self.assertEqual(property_product.bath, 3)
        self.assertEqual(property_product.squarefeet, 3200)
        self.assertEqual(property_product.garages, 2)
        self.assertEqual(property_product.year_built, 2022)
        self.assertEqual(property_product.land_size, 5000)
        self.assertEqual(property_product.salesperson_id, self.user_internal)
        self.assertEqual(len(property_product.amenity_ids), 2)
        self.assertIn(self.amenity_pool, property_product.amenity_ids)
        self.assertIn(self.amenity_garden, property_product.amenity_ids)

    def test_05_property_amenities_relation(self):
        """Test adding, modifying, and removing amenities on property template."""
        prop = self.ProductTemplate.create({
            'name': 'Downtown Studio Apt',
            'is_property': True,
            'listing_type': 'rent',
            'property_type': 'studio',
        })
        self.assertFalse(prop.amenity_ids)

        # Add amenities
        prop.write({'amenity_ids': [(4, self.amenity_pool.id)]})
        self.assertEqual(prop.amenity_ids.ids, [self.amenity_pool.id])

        prop.write({'amenity_ids': [(4, self.amenity_garden.id)]})
        self.assertEqual(set(prop.amenity_ids.ids), {self.amenity_pool.id, self.amenity_garden.id})

        # Remove an amenity
        prop.write({'amenity_ids': [(3, self.amenity_pool.id)]})
        self.assertEqual(prop.amenity_ids.ids, [self.amenity_garden.id])

    def test_06_preloaded_amenity_and_property_data(self):
        """Verify XML records provided by the theme are successfully registered and valid."""
        # 1. Amenity data
        smoke_alarm = self.env.ref('theme_livelo.amenity_smoke_alarm', raise_if_not_found=False)
        self.assertTrue(smoke_alarm, "Amenity 'amenity_smoke_alarm' should exist")
        self.assertEqual(smoke_alarm.name, 'Smoke Alarm')

        gym = self.env.ref('theme_livelo.amenity_gym', raise_if_not_found=False)
        self.assertTrue(gym, "Amenity 'amenity_gym' should exist")
        self.assertEqual(gym.name, 'Gym')

        wifi = self.env.ref('theme_livelo.amenity_wifi', raise_if_not_found=False)
        self.assertTrue(wifi, "Amenity 'amenity_wifi' should exist")
        self.assertEqual(wifi.name, 'Free WiFi')

        # 2. Mailing list data
        mailing_list = self.env.ref('theme_livelo.mailing_list_livelo', raise_if_not_found=False)
        self.assertTrue(mailing_list, "Mailing list 'mailing_list_livelo' should exist")
        self.assertEqual(mailing_list.name, 'Livelo Newsletter')
        self.assertTrue(mailing_list.is_public)

        # 3. Property data
        prop1 = self.env.ref('theme_livelo.product_property_1', raise_if_not_found=False)
        self.assertTrue(prop1, "Product 'product_property_1' should exist")
        self.assertTrue(prop1.is_property)
        self.assertEqual(prop1.listing_type, 'sale')
        self.assertEqual(prop1.property_type, 'house')
        self.assertEqual(prop1.bed, 3)
        self.assertEqual(prop1.bath, 2)
