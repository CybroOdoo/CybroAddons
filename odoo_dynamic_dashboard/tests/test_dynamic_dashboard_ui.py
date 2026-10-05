import json
from unittest.mock import patch

from odoo import Command
from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.odoo_dynamic_dashboard.models.dynamic_dashboard_ai import (
    DynamicDashboardAiGenerator,
)

JS_HELPERS = """
    const waitFor = (selector, { text } = {}) => new Promise((resolve, reject) => {
        const start = Date.now();
        const interval = setInterval(() => {
            const element = [...document.querySelectorAll(selector)].find(
                (el) => !text || el.textContent.includes(text)
            );
            if (element) {
                clearInterval(interval);
                resolve(element);
            } else if (Date.now() - start > 15000) {
                clearInterval(interval);
                reject(new Error(`Element not found: ${selector} ${text || ''}`));
            }
        }, 50);
    });
    const waitUntil = (condition, message) => new Promise((resolve, reject) => {
        const start = Date.now();
        const interval = setInterval(() => {
            if (condition()) {
                clearInterval(interval);
                resolve();
            } else if (Date.now() - start > 15000) {
                clearInterval(interval);
                reject(new Error(message));
            }
        }, 50);
    });
    const typeIn = (input, value) => {
        input.value = value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    };
    const dragBlock = (blockType, target) => {
        const dataTransfer = new DataTransfer();
        dataTransfer.setData('application/x-odoo-dynamic-dashboard-block', blockType);
        const eventInit = { bubbles: true, cancelable: true, dataTransfer, clientX: 99999 };
        target.dispatchEvent(new DragEvent('dragover', eventInit));
        target.dispatchEvent(new DragEvent('drop', eventInit));
    };
    const chooseModel = async (search, modelClass) => {
        const input = await waitFor('.o_dynamic_dashboard_configurator .o_dynamic_dashboard_model_selector input');
        input.focus();
        typeIn(input, search);
        (await waitFor(`.${modelClass}`)).click();
    };
"""


@tagged('post_install', '-at_install')
class TestDynamicDashboardUi(HttpCase):

    def test_dashboard_viewer(self):
        partner_model = self.env['ir.model']._get('res.partner')
        self.env['dynamic.dashboard'].with_user(self.env.ref('base.user_admin')).create({
            'name': 'UI Dashboard',
            'block_ids': [
                Command.create({'model_id': partner_model.id, 'block_type': 'tile'}),
                Command.create({
                    'model_id': partner_model.id,
                    'block_type': 'bar',
                    'group_by_field_id': self.env['ir.model.fields']._get('res.partner', 'type').id,
                }),
                Command.create({'block_type': 'text', 'name': 'Notes', 'text_content': 'Hello'}),
            ],
        })
        code = """
            const grid = document.querySelector('.o_dynamic_dashboard_grid');
            if (grid.querySelectorAll('.o_dynamic_dashboard_cell').length !== 3) {
                throw new Error('Expected 3 blocks');
            }
            if (!grid.querySelector('.o_dynamic_dashboard_chart canvas')) {
                throw new Error('Chart not rendered');
            }
            if (!grid.querySelector('.o_dynamic_dashboard_text_title')) {
                throw new Error('Text block not rendered');
            }
            console.log('test successful');
        """
        self.browser_js(
            f'/odoo/action-{self.env.ref("odoo_dynamic_dashboard.dynamic_dashboard_action_client").id}', code,
            ready="!!document.querySelector('.o_dynamic_dashboard_tile_value')",
            login='admin',
        )

    def test_builder_flow(self):
        """ Create a dashboard: drag blocks, choose their data, arrange them, save it
        and add it to a menu, from which it is then opened. """
        builder_action = self.env.ref('odoo_dynamic_dashboard.dynamic_dashboard_action_builder')
        code = JS_HELPERS + """
            (async () => {
                typeIn(document.querySelector('.o_dynamic_dashboard_name_input'), 'Sales Cockpit');

                // a KPI tile on contacts
                dragBlock('tile', await waitFor('.o_dynamic_dashboard_empty_drop'));
                await chooseModel('Contact', 'o_model_selector_res_partner');
                await waitFor('.o_dynamic_dashboard_tile_value');

                // a bar chart, preconfigured with a grouping once its model is chosen
                dragBlock('bar', await waitFor('.o_dynamic_dashboard_cell'));
                await waitFor('.o_dynamic_dashboard_configurator h5', { text: 'Bar Chart' });
                await chooseModel('Contact', 'o_model_selector_res_partner');
                await waitFor('.o_dynamic_dashboard_block_bar .o_dynamic_dashboard_chart canvas');

                // a text block
                document.querySelector('.o_dynamic_dashboard_palette_item[data-block-type="text"]').click();
                await waitUntil(
                    () => document.querySelectorAll('.o_dynamic_dashboard_cell').length === 3,
                    'The text block was not added'
                );

                document.querySelector('.o_dynamic_dashboard_auto_arrange').click();
                await waitUntil(() => {
                    const cells = [...document.querySelectorAll('.o_dynamic_dashboard_cell')];
                    return cells.every((cell) => cell.dataset.width === '12')
                        && cells[0].querySelector('.o_dynamic_dashboard_block_tile');
                }, 'Blocks were not auto arranged');

                document.querySelector('.o_dynamic_dashboard_save').click();
                const confirm = await waitFor('.o_dynamic_dashboard_menu_confirm');
                typeIn(document.querySelector('#o_dd_menu_name'), 'Cockpit');
                const parentSelect = document.querySelector('#o_dd_menu_parent');
                const parentOption = [...parentSelect.options].find((option) => option.text === 'Dynamic Dashboard Studio');
                parentSelect.value = parentOption.value;
                parentSelect.dispatchEvent(new Event('change', { bubbles: true }));
                confirm.click();

                // the dashboard is now opened from its own menu item
                await waitFor('.o_menu_sections', { text: 'Cockpit' });
                await waitFor('.o_breadcrumb', { text: 'Cockpit' });
                await waitFor('.o_dynamic_dashboard_edit');
                await waitFor('.o_dynamic_dashboard_tile_value');
                if (document.querySelector('.o_dynamic_dashboard_switcher')) {
                    throw new Error('A dashboard opened from its menu does not offer to switch dashboards');
                }
                console.log('test successful');
            })().catch((error) => console.error(error.message));
        """
        self.browser_js(
            f'/odoo/action-{builder_action.id}', code,
            ready="!!document.querySelector('.o_dynamic_dashboard_palette_item')",
            login='admin',
        )
        dashboard = self.env['dynamic.dashboard'].search([('name', '=', 'Sales Cockpit')])
        self.assertEqual(dashboard.block_ids.sorted().mapped('block_type'), ['tile', 'bar', 'text'])
        self.assertEqual(dashboard.menu_id.name, 'Cockpit')
        self.assertEqual(
            dashboard.menu_id.parent_id, self.env.ref('odoo_dynamic_dashboard.odoo_dynamic_dashboard_menu_root'),
        )

    def test_generate_with_ai(self):
        """ Describe a dashboard, let the AI design it, then save it. """
        design = {
            "name": "Contacts by AI",
            "blocks": [
                {"block_type": "tile", "name": "Contacts", "model": "res.partner"},
                {"block_type": "bar", "name": "Contacts by type", "model": "res.partner", "group_by": "type"},
            ],
        }
        builder_action = self.env.ref('odoo_dynamic_dashboard.dynamic_dashboard_action_builder')
        code = JS_HELPERS + """
            (async () => {
                (await waitFor('.o_dynamic_dashboard_empty_generate_ai')).click();
                typeIn(await waitFor('.o_dynamic_dashboard_ai_description'), 'Overview of our contacts');
                (await waitFor('.o_dynamic_dashboard_ai_block_count [data-block-count="3"]')).click();
                await waitFor('.o_dynamic_dashboard_ai_block_count [data-block-count="3"].btn-primary');
                (await waitFor('.o_dynamic_dashboard_ai_generate:not([disabled])')).click();
                // the AI only found 2 of the 3 blocks asked: the user is told
                await waitFor('.o_notification', { text: '2 of the 3' });

                await waitFor('.o_dynamic_dashboard_block_tile .o_dynamic_dashboard_tile_value');
                await waitFor('.o_dynamic_dashboard_block_bar .o_dynamic_dashboard_chart canvas');
                if (document.querySelector('.o_dynamic_dashboard_name_input').value !== 'Contacts by AI') {
                    throw new Error('The dashboard name was not suggested');
                }
                document.querySelector('.o_dynamic_dashboard_save').click();
                (await waitFor('.o_dynamic_dashboard_menu_dialog')).closest('.modal').querySelector('.btn-secondary').click();
                await waitFor('.o_dynamic_dashboard_edit');
                console.log('test successful');
            })().catch((error) => console.error(error.message));
        """
        # the AI designs 2 of the 3 blocks asked, and none more when asked for the missing one
        answers = ['["res.partner"]', json.dumps(design), json.dumps({"blocks": []})]
        with patch.object(DynamicDashboardAiGenerator, '_olg_chat', side_effect=answers) as olg_chat:
            self.browser_js(
                f'/odoo/action-{builder_action.id}', code,
                ready="!!document.querySelector('.o_dynamic_dashboard_palette_item')",
                login='admin',
            )
        self.assertIn("exactly 3 blocks", olg_chat.call_args_list[1].args[0])
        dashboard = self.env['dynamic.dashboard'].search([('name', '=', 'Contacts by AI')])
        self.assertEqual(dashboard.block_ids.sorted().mapped('block_type'), ['tile', 'bar'])

    def _create_presentable_dashboard(self):
        partner_model = self.env['ir.model']._get('res.partner')
        type_field = self.env['ir.model.fields']._get('res.partner', 'type')
        return self.env['dynamic.dashboard'].with_user(self.env.ref('base.user_admin')).create({
            'name': 'Presentable',
            'block_ids': [
                Command.create({'model_id': partner_model.id, 'block_type': 'tile'}),
                Command.create({'model_id': partner_model.id, 'block_type': 'gauge', 'target_value': 10}),
                Command.create({'block_type': 'text', 'name': 'Details', 'text_content': 'Breakdown'}),
                Command.create({'model_id': partner_model.id, 'block_type': 'bar', 'group_by_field_id': type_field.id}),
            ],
        })

    def test_present_as_slides(self):
        dashboard = self._create_presentable_dashboard()
        code = JS_HELPERS + """
            (async () => {
                const press = (key) => window.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }));
                const counter = () => document.querySelector('.o_dynamic_dashboard_slide_counter').textContent.replace(/\\s/g, '');
                (await waitFor('.o_dynamic_dashboard_present')).click();

                // title, key figures (tile + gauge), section, chart
                await waitFor('.o_dynamic_dashboard_slide_title', { text: 'Presentable' });
                await waitUntil(() => counter() === '1/4', 'Expected 4 slides');
                press('ArrowRight');
                await waitFor('.o_dynamic_dashboard_slide_kpis .o_dynamic_dashboard_tile_value');
                if (!document.querySelector('.o_dynamic_dashboard_slide_kpis .o_dynamic_dashboard_gauge')) {
                    throw new Error('Key figures are gathered on one slide');
                }
                document.querySelector('.o_dynamic_dashboard_slide_next').click();
                await waitFor('.o_dynamic_dashboard_slide_section .o_dynamic_dashboard_slide_title', { text: 'Details' });
                press('ArrowRight');
                await waitFor('.o_dynamic_dashboard_slide_block .o_dynamic_dashboard_chart canvas');
                press('ArrowLeft');
                await waitUntil(() => counter() === '3/4', 'Going back failed');
                press('Escape');
                await waitUntil(() => !document.querySelector('.o_dynamic_dashboard_presentation'), 'Escape did not close');
                console.log('test successful');
            })().catch((error) => console.error(error.message));
        """
        self.assertTrue(dashboard)
        self.browser_js(
            f'/odoo/action-{self.env.ref("odoo_dynamic_dashboard.dynamic_dashboard_action_client").id}', code,
            ready="!!document.querySelector('.o_dynamic_dashboard_present')", login='admin',
        )

    def test_export_pdf(self):
        self._create_presentable_dashboard()
        code = JS_HELPERS + """
            (async () => {
                const originalTitle = document.title;
                let printed = null;
                window.print = () => {
                    printed = {
                        title: document.title,
                        printing: document.body.classList.contains('o_dynamic_dashboard_printing'),
                        header: document.querySelector('.o_dynamic_dashboard_print_header')?.textContent || '',
                        page: [...document.querySelectorAll('style')].some((s) => s.textContent.includes('A4 landscape')),
                    };
                };
                (await waitFor('.o_dynamic_dashboard_export_pdf')).click();
                await waitUntil(() => printed, 'The print dialog was not opened');
                if (printed.title !== 'Presentable' || !printed.printing || !printed.page) {
                    throw new Error('Not laid out for the PDF: ' + JSON.stringify(printed));
                }
                if (!printed.header.includes('Presentable')) {
                    throw new Error('The PDF header misses the dashboard name');
                }
                if (document.title !== originalTitle || document.body.classList.contains('o_dynamic_dashboard_printing')) {
                    throw new Error('The page was not restored after printing');
                }
                console.log('test successful');
            })().catch((error) => console.error(error.message));
        """
        self.browser_js(
            f'/odoo/action-{self.env.ref("odoo_dynamic_dashboard.dynamic_dashboard_action_client").id}', code,
            ready="!!document.querySelector('.o_dynamic_dashboard_export_pdf')", login='admin',
        )

    def test_filter_block(self):
        self._create_presentable_dashboard()
        code = JS_HELPERS + """
            (async () => {
                const bar = await waitFor('.o_dynamic_dashboard_block_bar');
                await waitFor('.o_dynamic_dashboard_block_bar .o_dynamic_dashboard_chart canvas');
                const chartLabels = () => Chart.getChart(bar.querySelector('canvas')).data.labels;
                const initialLabels = chartLabels().length;
                bar.querySelector('.o_dynamic_dashboard_block_filter').click();

                // values of the grouping, from the data of the block
                const options = await waitFor('.o_dynamic_dashboard_filter_panel .o_dd_filter_value');
                const label = options.textContent.trim();
                options.querySelector('input').click();
                await waitUntil(
                    () => bar.querySelector('.o_dynamic_dashboard_filter_summary')?.textContent.includes(label),
                    'The filter summary is not shown'
                );
                await waitUntil(() => {
                    const canvas = bar.querySelector('canvas');
                    return canvas && Chart.getChart(canvas)?.data.labels.length === 1;
                }, 'The block was not filtered');
                if (bar.querySelector('.o_dynamic_dashboard_block_filter .badge').textContent.trim() !== '1') {
                    throw new Error('The number of active filters is not shown');
                }

                // period on a date field of the model
                document.querySelector('.o_dynamic_dashboard_filter_periods [data-period="this_year"]').click();
                await waitUntil(
                    () => bar.querySelector('.o_dynamic_dashboard_block_filter .badge')?.textContent.trim() === '2',
                    'The period filter is not counted'
                );

                // the filters of the viewer are kept in the browser
                const stored = JSON.parse(localStorage.getItem('odoo_dynamic_dashboard.filters'));
                if (!Object.values(stored).some((blocks) => Object.keys(blocks).length === 1)) {
                    throw new Error('The filters were not stored');
                }

                // two changes in a row (no render in between) both apply
                document.querySelector('.o_dd_filter_clear').click();
                await waitUntil(() => !bar.querySelector('.o_dynamic_dashboard_filter_summary'), 'Filters not cleared');
                document.querySelector('.o_dd_filter_value input').click();
                document.querySelector('.o_dynamic_dashboard_filter_periods [data-period="this_month"]').click();
                await waitUntil(
                    () => bar.querySelector('.o_dynamic_dashboard_block_filter .badge')?.textContent.trim() === '2',
                    'A quick second change discarded the first one'
                );

                document.querySelector('.o_dd_filter_clear').click();
                await waitUntil(() => !bar.querySelector('.o_dynamic_dashboard_filter_summary'), 'Filters not cleared');
                await waitUntil(() => {
                    const canvas = bar.querySelector('canvas');
                    return canvas && Chart.getChart(canvas)?.data.labels.length === initialLabels;
                }, 'The block was not restored');
                console.log('test successful');
            })().catch((error) => console.error(error.message));
        """
        self.browser_js(
            f'/odoo/action-{self.env.ref("odoo_dynamic_dashboard.dynamic_dashboard_action_client").id}', code,
            ready="!!document.querySelector('.o_dynamic_dashboard_block_filter')", login='admin',
        )

    def test_ai_analysis(self):
        self._create_presentable_dashboard()
        analysis = (
            "- Most contacts are invoice addresses.\n"
            "- Few delivery addresses.\n"
            "Recommendation: Complete the delivery addresses."
        )
        code = JS_HELPERS + """
            (async () => {
                const bar = await waitFor('.o_dynamic_dashboard_block_bar');
                bar.querySelector('.o_dynamic_dashboard_block_analyze').click();
                await waitFor('.o_dynamic_dashboard_ai_analysis_points li', { text: 'Most contacts are invoice addresses.' });
                const recommendation = await waitFor('.o_dynamic_dashboard_ai_analysis_recommendation');
                if (!recommendation.textContent.includes('Complete the delivery addresses.')) {
                    throw new Error('The recommendation is not shown');
                }
                if (document.querySelectorAll('.o_dynamic_dashboard_ai_analysis_points li').length !== 2) {
                    throw new Error('Expected 2 points');
                }
                document.querySelector('.modal-footer .btn-primary').click();
                await waitUntil(() => !document.querySelector('.o_dynamic_dashboard_ai_analysis'), 'Not closed');

                // reopened: the analysis is reused while the data of the block did not change
                bar.querySelector('.o_dynamic_dashboard_block_analyze').click();
                await waitFor('.o_dynamic_dashboard_ai_analysis_points li');
                console.log('test successful');
            })().catch((error) => console.error(error.message));
        """
        with patch.object(DynamicDashboardAiGenerator, '_olg_chat', return_value=analysis) as olg_chat:
            self.browser_js(
                f'/odoo/action-{self.env.ref("odoo_dynamic_dashboard.dynamic_dashboard_action_client").id}', code,
                ready="!!document.querySelector('.o_dynamic_dashboard_block_analyze')", login='admin',
            )
        self.assertEqual(olg_chat.call_count, 1)
        self.assertIn("Contact", olg_chat.call_args.args[0])

    def test_builder_as_dashboard_user(self):
        """ A dashboard user builds and saves a dashboard; putting it in a menu is left to
        the administrators. """
        new_test_user(self.env, login='ui_dashboard_user', groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user')
        builder_action = self.env.ref('odoo_dynamic_dashboard.dynamic_dashboard_action_builder')
        code = JS_HELPERS + """
            (async () => {
                typeIn(document.querySelector('.o_dynamic_dashboard_name_input'), 'My own KPIs');
                document.querySelector('.o_dynamic_dashboard_palette_item[data-block-type="tile"]').click();
                await chooseModel('Contact', 'o_model_selector_res_partner');
                await waitFor('.o_dynamic_dashboard_tile_value');
                document.querySelector('.o_dynamic_dashboard_save').click();
                await waitFor('.o_notification', { text: 'Ask a dashboard administrator' });
                await waitFor('.o_dynamic_dashboard_edit');
                if (document.querySelector('.o_dynamic_dashboard_menu_dialog')) {
                    throw new Error('Only administrators are asked to add the dashboard to a menu');
                }
                if ([...document.querySelectorAll('.o_control_panel button')].some((b) => b.textContent.includes('Add to Menu'))) {
                    throw new Error('Only administrators can add the dashboard to a menu');
                }
                console.log('test successful');
            })().catch((error) => console.error(error.message));
        """
        self.browser_js(
            f'/odoo/action-{builder_action.id}', code,
            ready="!!document.querySelector('.o_dynamic_dashboard_palette_item')", login='ui_dashboard_user',
        )
        dashboard = self.env['dynamic.dashboard'].search([('name', '=', 'My own KPIs')])
        self.assertEqual(dashboard.user_id.login, 'ui_dashboard_user')
        self.assertFalse(dashboard.menu_id)

    def test_menu_dashboard_as_employee(self):
        """ An employee opens a dashboard from its menu: read only, filters and slides available. """
        new_test_user(self.env, login='ui_employee', groups='base.group_user')
        dashboard = self._create_presentable_dashboard()
        menu_id = dashboard.set_dashboard_menu('Team KPIs', False, group_ids=self.env.ref('base.group_user').ids)
        action = self.env['ir.ui.menu'].browse(menu_id).action
        code = JS_HELPERS + """
            (async () => {
                await waitFor('.o_main_navbar', { text: 'Team KPIs' });
                await waitFor('.o_dynamic_dashboard_block_bar canvas');
                for (const selector of ['.o_dynamic_dashboard_edit', '.o_dynamic_dashboard_switcher']) {
                    if (document.querySelector(selector)) {
                        throw new Error(`An employee must not see ${selector}`);
                    }
                }
                if (document.querySelectorAll('.o_dynamic_dashboard_block_filter').length !== 3) {
                    throw new Error('The data blocks can be filtered by the employee');
                }
                await waitFor('.o_dynamic_dashboard_present');
                console.log('test successful');
            })().catch((error) => console.error(error.message));
        """
        self.browser_js(
            f'/odoo/action-{action.id}', code,
            ready="!!document.querySelector('.o_dynamic_dashboard_tile_value')", login='ui_employee',
        )
