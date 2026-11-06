# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.addons.pharmaceutical_base.tests.common import PharmaTestCommon


class PharmaSopCommon(PharmaTestCommon):
    """A work centre, an employee per role user and helpers for SOPs."""

    @classmethod
    def setUpClass(cls):
        """Create the work centre and the employees of the operator and QA users."""
        super().setUpClass()
        cls.workcenter = cls.env['mrp.workcenter'].create({'name': 'Granulation Suite'})
        cls.other_workcenter = cls.env['mrp.workcenter'].create({'name': 'Coating Suite'})
        cls.operator_employee = cls.env['hr.employee'].create({
            'name': 'Pharma Operator', 'user_id': cls.operator.id,
        })
        cls.qa_employee = cls.env['hr.employee'].create({
            'name': 'Pharma QA', 'user_id': cls.qa_user.id,
        })

    @classmethod
    def create_sop(cls, name='Granulation', workcenter=None, employees=None):
        """Create a draft SOP, written by the operator."""
        return cls.env['pharma.sop'].with_user(cls.operator).create({
            'name': name,
            'workcenter_id': (workcenter or cls.workcenter).id,
            'employee_ids': [(6, 0, (employees or cls.operator_employee).ids)],
        }).with_user(cls.env.user)

    @classmethod
    def effective_sop(cls, name='Granulation', workcenter=None, employees=None):
        """Create an SOP and have QA approve it."""
        sop = cls.create_sop(name, workcenter, employees)
        sop.action_submit_review()
        sop.with_user(cls.qa_user).action_approve()
        return sop

    def training_of(self, sop, employee=None):
        """The active training record of ``employee`` (the operator) on ``sop``."""
        return self.env['pharma.training'].search([
            ('sop_id', '=', sop.id),
            ('employee_id', '=', (employee or self.operator_employee).id),
        ])

    def pass_training(self, training, score=90.0):
        """QA records a score on the training."""
        training.score = score
        training.with_user(self.qa_user).action_record_assessment()
