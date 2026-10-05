import json
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.odoo_dynamic_dashboard.models.dynamic_dashboard_ai import (
    DynamicDashboardAiGenerator,
)

DESIGN = {
    "name": "Contacts Overview",
    "blocks": [
        {"block_type": "text", "name": "Contacts", "text_content": "Who we work with"},
        {"block_type": "tile", "name": "Contacts", "model": "res.partner", "icon": "group"},
        {"block_type": "progress", "name": "Goal", "model": "res.partner", "target_value": 50},
        {"block_type": "pie", "name": "By type", "model": "res.partner", "group_by": "type",
         "domain": [["active", "=", True]]},
        {"block_type": "pivot", "name": "Type x country", "model": "res.partner", "group_by": "type",
         "sub_group_by": "country_id"},
        {"block_type": "record_list", "name": "Latest", "model": "res.partner",
         "list_fields": ["name", "email", "no_such_field"], "order_by": "create_date"},
        # invalid blocks, dropped
        {"block_type": "funnel", "model": "res.partner", "group_by": "type"},
        {"block_type": "bar", "model": "res.partner", "group_by": "no_such_field"},
        {"block_type": "bar", "model": "sale.nothing", "group_by": "type"},
        {"block_type": "gauge", "model": "res.partner"},
        {"block_type": "stacked_bar", "model": "res.partner", "group_by": "type"},
        "not a block",
    ],
}


@tagged('post_install', '-at_install')
class TestDynamicDashboardAi(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dashboard_user = new_test_user(
            cls.env, login='ai_user', groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user',
        )
        cls.Generator = cls.env['dynamic.dashboard.ai.generator'].with_user(cls.dashboard_user)

    def _generate(self, answers, description="Overview of our contacts"):
        with patch.object(DynamicDashboardAiGenerator, '_olg_chat', side_effect=answers) as olg_chat:
            result = self.env['dynamic.dashboard'].with_user(self.dashboard_user).generate_with_ai(description)
        return result, olg_chat

    def test_generate(self):
        result, olg_chat = self._generate([
            'Sure! ["res.partner", "not.a.model"]',
            f"Here is your dashboard:\n```json\n{json.dumps(DESIGN)}\n```",
        ])
        self.assertEqual(olg_chat.call_count, 2)
        self.assertIn("res.partner", olg_chat.call_args_list[0].args[0])
        self.assertIn("country_id", olg_chat.call_args_list[1].args[0], "fields of the chosen model are described")
        self.assertEqual(result['name'], "Contacts Overview")
        blocks = result['blocks']
        self.assertEqual(
            [block['block_type'] for block in blocks], ['text', 'tile', 'progress', 'pie', 'pivot', 'record_list'],
        )
        text, tile, progress, pie, pivot, record_list = blocks
        self.assertEqual(text['text_content'], "Who we work with")
        self.assertEqual((tile['model'], tile['icon'], tile['aggregate']), ('res.partner', 'group', 'count'))
        self.assertEqual(progress['target_value'], 50)
        self.assertEqual(pie['domain'], "[('active', '=', True)]")
        self.assertEqual((pivot['group_by'], pivot['sub_group_by']), ('type', 'country_id'))
        self.assertEqual(record_list['list_fields'], ['name', 'email'])

        # the generated blocks are valid builder configurations
        Block = self.env['dynamic.dashboard.block'].with_user(self.dashboard_user)
        for block in blocks:
            self.assertFalse(Block.preview_block(block)['error'], block['block_type'])
        saved = self.env['dynamic.dashboard'].with_user(self.dashboard_user).save_from_builder(
            {'name': result['name'], 'blocks': blocks},
        )
        self.assertEqual(len(saved['blocks']), 6)

    def test_block_count(self):
        answers = ['["res.partner"]', json.dumps(DESIGN)]
        with patch.object(DynamicDashboardAiGenerator, '_olg_chat', side_effect=answers) as olg_chat:
            result = self.env['dynamic.dashboard'].with_user(self.dashboard_user).generate_with_ai(
                "Overview of our contacts", block_count=3,
            )
        self.assertIn("exactly 3 blocks", olg_chat.call_args_list[1].args[0])
        # the first valid blocks proposed, never more than asked
        self.assertEqual([block['block_type'] for block in result['blocks']], ['text', 'tile', 'progress'])

        # too few blocks designed: the missing ones are asked once more
        first = {"name": "Short", "blocks": DESIGN["blocks"][:2]}
        more = {"blocks": [DESIGN["blocks"][3], DESIGN["blocks"][6], DESIGN["blocks"][5]]}
        answers = ['["res.partner"]', json.dumps(first), json.dumps(more)]
        with patch.object(DynamicDashboardAiGenerator, '_olg_chat', side_effect=answers) as olg_chat:
            result = self.env['dynamic.dashboard'].with_user(self.dashboard_user).generate_with_ai(
                "Overview of our contacts", block_count=4,
            )
        self.assertEqual(olg_chat.call_count, 3)
        follow_up = olg_chat.call_args_list[2].args[0]
        self.assertIn("exactly 2 block", follow_up)
        self.assertIn('tile "Contacts"', follow_up, "the AI is told which blocks exist already")
        self.assertEqual([block['block_type'] for block in result['blocks']], ['text', 'tile', 'pie', 'record_list'])

        _result, olg_chat = self._generate(['["res.partner"]', json.dumps(DESIGN)])
        self.assertIn("6 to 12 blocks", olg_chat.call_args_list[1].args[0], "the AI decides without a count")

        for block_count in (0, 21, "5"):
            with self.assertRaisesRegex(UserError, "between 1 and 20"):
                self.env['dynamic.dashboard'].with_user(self.dashboard_user).generate_with_ai(
                    "Contacts", block_count=block_count,
                )

    def test_candidate_models(self):
        candidates = self.Generator._get_candidate_models()
        self.assertIn('res.partner', candidates)
        self.assertFalse([name for name in candidates if name.startswith(('ir.', 'dynamic.dashboard'))])

    def test_invalid_answers(self):
        with self.assertRaisesRegex(UserError, "could not be understood"):
            self._generate(["I cannot help with that."])
        with self.assertRaisesRegex(UserError, "did not find data"):
            self._generate(['["unknown.model"]'])
        with self.assertRaisesRegex(UserError, "could not design"):
            self._generate(['["res.partner"]', json.dumps({"blocks": [{"block_type": "funnel"}]})])
        with self.assertRaisesRegex(UserError, "Describe"):
            self._generate([], description="  ")

    def test_access(self):
        employee = new_test_user(self.env, login='ai_employee', groups='base.group_user')
        with self.assertRaises(AccessError):
            self.env['dynamic.dashboard'].with_user(employee).generate_with_ai("Sales")


ANALYSIS = """- Invoice addresses are the most common, with 2 of the 3 contacts.
- Contact addresses come second with 1.
Recommendation: Review why delivery addresses are missing."""


@tagged('post_install', '-at_install')
class TestDynamicDashboardAiAnalysis(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dashboard_user = new_test_user(
            cls.env, login='analysis_user', groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user',
        )
        cls.partners = cls.env['res.partner'].create([
            {'name': 'Analysis A', 'type': 'invoice', 'color': 1},
            {'name': 'Analysis B', 'type': 'invoice', 'color': 2},
            {'name': 'Analysis C', 'type': 'contact', 'color': 3},
        ])
        domain = str([('id', 'in', cls.partners.ids)])
        Dashboard = cls.env['dynamic.dashboard'].with_user(cls.dashboard_user)
        data = Dashboard.save_from_builder({'name': 'Analyzed', 'blocks': [
            {'block_type': 'tile', 'model': 'res.partner', 'domain': domain},
            {'block_type': 'progress', 'model': 'res.partner', 'domain': domain, 'target_value': 6},
            {'block_type': 'bar', 'model': 'res.partner', 'domain': domain, 'group_by': 'type'},
            {'block_type': 'pivot', 'model': 'res.partner', 'domain': domain, 'group_by': 'type',
             'sub_group_by': 'color'},
            {'block_type': 'record_list', 'model': 'res.partner', 'domain': domain,
             'list_fields': ['name', 'type'], 'order_by': 'name', 'order_desc': False},
            {'block_type': 'text', 'name': 'Notes'},
            {'block_type': 'tile', 'model': 'res.partner', 'domain': "[('id', '=', 0)]"},
        ]})
        cls.blocks = cls.env['dynamic.dashboard.block'].with_user(cls.dashboard_user).browse(
            [block['id'] for block in data['blocks']],
        )

    def _analyze(self, block, **kwargs):
        with patch.object(DynamicDashboardAiGenerator, '_olg_chat', return_value=ANALYSIS) as olg_chat:
            result = block.get_ai_analysis(**kwargs)
        self.assertEqual(result['analysis'], ANALYSIS)
        return olg_chat.call_args.args[0]

    def test_prompts(self):
        tile, progress, bar, pivot, record_list = self.blocks[:5]
        prompt = self._analyze(tile)
        self.assertIn("Value: 3", prompt)
        self.assertIn("Answer in English", prompt)
        self.assertIn("Recommendation:", prompt)

        self.assertIn("Target: 6 (50% reached)", self._analyze(progress))

        prompt = self._analyze(bar)
        self.assertIn("- Invoice: 2", prompt)
        self.assertIn("- Contact: 1", prompt)
        self.assertIn("Grouped by: Address Type", prompt)

        prompt = self._analyze(pivot)
        self.assertIn("Then split by: Color Index", prompt)
        self.assertRegex(prompt, r"- Invoice: (1=1, 2=1|2=1, 1=1)")

        prompt = self._analyze(record_list)
        self.assertIn("Columns: Name | Address Type", prompt)
        self.assertIn("Analysis A | Invoice", prompt)

    def test_filtered_analysis(self):
        bar = self.blocks[2]
        prompt = self._analyze(bar, filter_domain=[('type', '=', 'invoice')], filter_summary="Invoice")
        self.assertIn("- Invoice: 2", prompt)
        self.assertNotIn("- Contact", prompt)
        self.assertIn("Filters applied by the viewer: Invoice", prompt)

    def test_nothing_to_analyze(self):
        text = self.blocks[5]
        with self.assertRaisesRegex(UserError, "text block"):
            text.get_ai_analysis()
        with patch.object(DynamicDashboardAiGenerator, '_olg_chat') as olg_chat:
            with self.assertRaisesRegex(UserError, "no data"):
                self.blocks[2].get_ai_analysis(filter_domain=[('id', '=', 0)])
            olg_chat.assert_not_called()

    def test_access(self):
        employee = new_test_user(self.env, login='analysis_employee', groups='base.group_user')
        with self.assertRaises(AccessError):
            self.blocks[0].with_user(employee).get_ai_analysis()
