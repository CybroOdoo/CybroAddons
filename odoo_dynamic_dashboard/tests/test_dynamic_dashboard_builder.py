from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestDynamicDashboardBuilder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(
            cls.env, login='builder_manager',
            groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_manager',
        )
        cls.dashboard_user = new_test_user(
            cls.env, login='builder_user', groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user',
        )
        cls.partners = cls.env['res.partner'].create([
            {'name': 'Builder A', 'type': 'invoice', 'color': 1},
            {'name': 'Builder B', 'type': 'invoice', 'color': 2},
            {'name': 'Builder C', 'type': 'contact', 'color': 2},
        ])
        cls.domain = str([('id', 'in', cls.partners.ids)])
        cls.Block = cls.env['dynamic.dashboard.block']
        cls.Dashboard = cls.env['dynamic.dashboard']

    def _config(self, **values):
        return {'block_type': 'tile', 'model': 'res.partner', 'domain': self.domain, **values}

    def _preview(self, **values):
        data = self.Block.with_user(self.dashboard_user).preview_block(self._config(**values))
        self.assertFalse(data['error'])
        return data

    def test_preview_value_blocks(self):
        self.assertEqual(self._preview()['value'], 3)
        data = self._preview(block_type='progress', aggregate='sum', measure='color', target_value=10)
        self.assertEqual(data['value'], 5)
        self.assertEqual(data['name'], "Total Color Index")

    def test_preview_series(self):
        data = self._preview(block_type='hbar', group_by='type')
        self.assertEqual(dict(zip(data['labels'], data['series'][0]['values'])), {'Invoice': 2, 'Contact': 1})
        self.assertEqual(data['name'], "Contact Count by Address Type")

    def test_preview_sub_grouped(self):
        data = self._preview(block_type='pivot', group_by='type', sub_group_by='color')
        self.assertEqual(data['labels'], ['Invoice', 'Contact'])
        series = {serie['label']: serie['values'] for serie in data['series']}
        self.assertEqual(series, {'2': [1, 1], '1': [1, 0]})
        cell_domain = data['series'][0]['domains'][0]
        self.assertEqual(self.env['res.partner'].search(cell_domain), self.partners[1])

        with self.assertRaises(ValidationError):
            self.Block.create({
                'dashboard_id': self.Dashboard.create({'name': 'D'}).id,
                'block_type': 'stacked_bar',
                'model_id': self.env['ir.model']._get_id('res.partner'),
                'group_by_field_id': self.env['ir.model.fields']._get('res.partner', 'type').id,
            })

    def test_preview_record_list(self):
        data = self._preview(block_type='record_list', list_fields=['name', 'type'], order_by='name', order_desc=False)
        self.assertEqual([column['name'] for column in data['columns']], ['name', 'type'])
        self.assertEqual([row['values'] for row in data['rows']], [
            ['Builder A', 'Invoice'], ['Builder B', 'Invoice'], ['Builder C', 'Contact'],
        ])

    def test_preview_unconfigured(self):
        data = self.Block.preview_block({'block_type': 'bar', 'model': False})
        self.assertTrue(data['error'])
        data = self.Block.preview_block({'block_type': 'text', 'name': 'Sales', 'text_content': 'Hello'})
        self.assertFalse(data['error'])

    def test_save_from_builder(self):
        Dashboard = self.Dashboard.with_user(self.dashboard_user)
        data = Dashboard.save_from_builder({
            'id': False,
            'name': 'Built',
            'blocks': [
                self._config(name='Partners'),
                self._config(block_type='bar', group_by='type', width=6),
                {'block_type': 'text', 'name': 'Notes', 'text_content': 'Hello'},
            ],
        })
        dashboard = Dashboard.browse(data['id'])
        self.assertEqual(dashboard.name, 'Built')
        self.assertEqual(dashboard.block_ids.mapped('block_type'), ['tile', 'bar', 'text'])
        self.assertEqual(dashboard.block_ids[1].width, '6')
        self.assertFalse(data['menu_id'])

        tile, bar, text = data['blocks']
        Dashboard.save_from_builder({
            'id': dashboard.id,
            'name': 'Built again',
            'blocks': [{**bar, 'width': 12}, {**tile, 'name': 'All partners'}],
        })
        self.assertEqual(dashboard.name, 'Built again')
        blocks = dashboard.block_ids.sorted()
        self.assertEqual(blocks.mapped('block_type'), ['bar', 'tile'])
        self.assertEqual(blocks.ids, [bar['id'], tile['id']])
        self.assertEqual(blocks[1].name, 'All partners')
        self.assertFalse(self.Block.browse(text['id']).exists())

    def test_set_dashboard_menu(self):
        parent = self.env.ref('odoo_dynamic_dashboard.odoo_dynamic_dashboard_menu_root')
        data = self.Dashboard.with_user(self.manager).save_from_builder({'name': 'Sales', 'blocks': [self._config()]})
        dashboard = self.Dashboard.with_user(self.manager).browse(data['id'])
        menu_id = dashboard.set_dashboard_menu('Sales KPIs', parent.id)
        menu = self.env['ir.ui.menu'].browse(menu_id)
        self.assertEqual(menu.name, 'Sales KPIs')
        self.assertEqual(menu.parent_id, parent)
        self.assertEqual(menu.action.params, {'dashboard_id': dashboard.id})
        self.assertEqual(dashboard.get_dashboard_data()['menu_name'], 'Sales KPIs')

        own = self.Dashboard.with_user(self.dashboard_user).create({'name': 'Mine'})
        with self.assertRaises(AccessError):
            own.set_dashboard_menu('Mine', parent.id)

    def test_filtered_block_data(self):
        dashboard = self.Dashboard.with_user(self.dashboard_user).create({'name': 'Filtered'})
        data = dashboard.save_from_builder({'id': dashboard.id, 'name': 'Filtered', 'blocks': [
            self._config(),
            self._config(block_type='bar', group_by='type'),
        ]})
        tile, bar = data['blocks']
        self.assertEqual(len(bar['label_domains']), 2, "the domain of each group is given to filter on it")
        Block = self.Block.with_user(self.dashboard_user)

        filtered = Block.browse(tile['id']).get_block_data_filtered([('type', '=', 'invoice')])
        self.assertEqual(filtered['value'], 2)
        self.assertIn(('type', '=', 'invoice'), [tuple(leaf) for leaf in filtered['record_domain'] if isinstance(leaf, (list, tuple))])

        invoice_domain = bar['label_domains'][bar['labels'].index('Invoice')]
        filtered = Block.browse(bar['id']).get_block_data_filtered(invoice_domain)
        self.assertEqual(filtered['labels'], ['Invoice'])
        self.assertEqual(filtered['series'][0]['values'], [2])

        self.assertEqual(Block.browse(tile['id']).get_block_data_filtered([])['value'], 3)
        self.assertTrue(Block.browse(tile['id']).get_block_data_filtered([('no_such_field', '=', 1)])['error'])
