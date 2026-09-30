/** @odoo-module **/

export class NodeTemplates {
    constructor(workflowBuilder) {
        this.workflow = workflowBuilder;
        this.state = workflowBuilder.state;
    }

    getNodeIcon(type) {
        const icons = {
            start: '▶️', end: '🏁', automation: '⚙️', endpoint: '🌐',
            auth: '🔐', get: '📥', post: '📤', put: '✏️', delete: '🗑️',
            condition: '❓', loop: '🔁', orm: "🗄️",
        };
        return icons[type] || '🔘';
    }

    getNodeTitle(type) {
        const titles = {
            start: 'Start', end: 'End', automation: 'Automation',
            endpoint: 'API Endpoint', auth: 'Authentication',
            get: 'GET Request', post: 'POST Request', put: 'PUT Request',
            delete: 'DELETE Request', condition: 'Condition',
            loop: 'Loop', orm: "ORM Operation",
        };
        return titles[type] || 'Node';
    }

    getDefaultConfig(type) {
        switch (type) {
            case 'start':
            case 'end':
                return {};
            case 'endpoint':
                return { baseUrl: '', authType: 'none', apiPlatform: 'generic' };
            case 'loop':
                return { loopType: 'foreach', collectionPath: '' };
            case 'condition':
                return { sourceData: 'static', operator: 'equals', leftOperand: '', rightOperand: '' };
            case "orm":
                return { model: "", operation: "create", ormFields: [], ormDomains: [], field_values_json: "{}" };
            case 'get':
            case 'post':
            case 'put':
            case 'delete':
                return { url: '', timeout: 10000, bodyType: 'json', body: '', authType: 'none' };
            default:
                return {};
        }
    }
}