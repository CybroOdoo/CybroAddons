# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import QualityCommon


@tagged('post_install', '-at_install', 'quality_assurance')
class TestQualitySecurity(QualityCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.quality_user = new_test_user(
            cls.env, login='qa_user',
            groups='base.group_user,quality_assurance.group_quality_user')

    def test_manager_group_implies_user_group(self):
        manager = self.env.ref('quality_assurance.group_quality_manager')
        user = self.env.ref('quality_assurance.group_quality_user')
        self.assertIn(user, manager.implied_ids)

    def test_quality_user_has_full_access_on_measure(self):
        measure = self.env['quality.measure'].with_user(
            self.quality_user).create({'name': 'User Measure'})
        self.assertEqual(measure.name, 'User Measure')
        measure.write({'name': 'Renamed'})
        measure.unlink()
        self.assertFalse(measure.exists())

    def test_quality_user_has_full_access_on_alert_and_test(self):
        alert = self.env['quality.alert'].with_user(
            self.quality_user).create({
                'name': 'User Alert',
                'product_id': self.product.id,
            })
        test = self.env['quality.test'].with_user(
            self.quality_user).create({
                'quality_measure_id': self.measure_qty.id,
                'alert_id': alert.id,
            })
        test.unlink()
        alert.unlink()
        self.assertFalse(alert.exists())
