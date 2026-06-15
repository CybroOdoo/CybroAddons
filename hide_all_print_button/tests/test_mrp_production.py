# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMrpProduction(TransactionCase):

    def _create_print_action(self):
        model = self.env["ir.model"]._get("mrp.production")
        return self.env["ir.actions.report"].create({
            "name": "Hide Print Button Test Report",
            "model": "mrp.production",
            "report_name": "hide_all_print_button.test_report",
            "binding_model_id": model.id,
            "binding_type": "report",
            "binding_view_types": "form,list",
        })

    def _get_print_toolbar(self):
        views = self.env["mrp.production"].get_views(
            [(False, "form"), (False, "list")],
            {"toolbar": True},
        )["views"]
        return {
            view_type: views[view_type]["toolbar"].get("print", [])
            for view_type in ("form", "list")
        }

    def _assert_print_buttons_are_hidden(self):
        self._create_print_action()
        self.env.user.write({
            "hide_mrp_print": False,
            "hide_mrp_production_print": False,
        })

        visible_toolbar = self._get_print_toolbar()
        self.assertTrue(visible_toolbar["form"])
        self.assertTrue(visible_toolbar["list"])

        self.env.user.write({
            "hide_mrp_print": True,
            "hide_mrp_production_print": True,
        })
        hidden_toolbar = self._get_print_toolbar()

        self.assertEqual(hidden_toolbar["form"], [])
        self.assertEqual(hidden_toolbar["list"], [])

    def test_get_views_hides_mrp_production_print_buttons(self):
        self._assert_print_buttons_are_hidden()
