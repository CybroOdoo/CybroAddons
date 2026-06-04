from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee_cc_1 = cls.env['hr.employee'].create({
            'name': 'Timesheet CC Employee 1',
            'work_email': 'timesheet.cc.1@example.com',
        })
        cls.employee_cc_2 = cls.env['hr.employee'].create({
            'name': 'Timesheet CC Employee 2',
            'work_email': 'timesheet.cc.2@example.com',
        })

    def test_set_values_stores_cc_employee_ids(self):
        settings = self.env['res.config.settings'].create({
            'employee_ids': [
                (6, 0, [self.employee_cc_1.id, self.employee_cc_2.id]),
            ],
        })

        settings.set_values()

        employee_ids = self.env['ir.config_parameter'].sudo().get_param(
            'work_report_from_timesheet.employee_ids'
        )
        self.assertEqual(
            employee_ids,
            str([self.employee_cc_1.id, self.employee_cc_2.id])
        )

    def test_get_values_loads_cc_employee_ids(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'work_report_from_timesheet.employee_ids',
            [self.employee_cc_1.id, self.employee_cc_2.id],
        )

        values = self.env['res.config.settings'].get_values()

        self.assertEqual(values['employee_ids'], [
            (6, 0, [self.employee_cc_1.id, self.employee_cc_2.id]),
        ])

    def test_get_values_returns_false_without_cc_configuration(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'work_report_from_timesheet.employee_ids',
            '',
        )

        values = self.env['res.config.settings'].get_values()

        self.assertFalse(values['employee_ids'])
