from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_collection')
class TestInspectionLock(TransactionCase):
    """Passed and failed inspections are locked, with a proper message (not a NameError)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({'name': 'Insp Lock Waste', 'code': 'ILW'})
        cls.batch = cls.env['waste.batch'].create({'category_id': cls.category.id})
        cls.user = new_test_user(
            cls.env, login='insp_lock_user', groups='base.group_user,wm_base.group_wm_admin')

    def _inspection(self, state):
        return self.env['wm.batch.inspection'].create({'batch_id': self.batch.id, 'state': state})

    def test_edit_of_finished_inspection_is_blocked(self):
        for state in ('passed', 'failed'):
            inspection = self._inspection(state).with_user(self.user)
            with self.assertRaises(UserError, msg=state):
                inspection.write({'quality_grade': 'grade_a'})

    def test_delete_of_finished_inspection_is_blocked(self):
        for state in ('passed', 'failed'):
            inspection = self._inspection(state).with_user(self.user)
            with self.assertRaises(UserError, msg=state):
                inspection.unlink()

    def test_open_inspection_stays_editable(self):
        inspection = self._inspection('in_progress').with_user(self.user)
        inspection.write({'quality_grade': 'grade_b'})
        self.assertEqual(inspection.quality_grade, 'grade_b')
