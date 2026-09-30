/** @odoo-module **/

export class FormManager {
    constructor(workflowBuilder) {
        this.workflow = workflowBuilder;
        this.state = workflowBuilder.state;
        this.notification = workflowBuilder.notification;
    }

    updateBodyType(bodyType) {
        const nodeId = this.state.selectedNode;
        if (!nodeId) {
            console.error('❌ No node selected');
            return;
        }

        this.workflow.updateNodeConfig(nodeId, 'bodyType', bodyType);

        const nodeConfig = this.state.nodeConfigs[nodeId];

        if (bodyType === 'form') {
            if (!nodeConfig.config.formFields || !Array.isArray(nodeConfig.config.formFields)) {
                // FIX: Added nodeId as the first argument
                this.workflow.updateNodeConfig(nodeId, 'formFields', []);
            }

            // Re-fetch config after update to ensure we have the array
            const updatedConfig = this.state.nodeConfigs[nodeId];

            if (updatedConfig.config.formFields.length === 0) {
                this.addFormField();
            }

            if (updatedConfig.config.body && updatedConfig.config.body.trim()) {
                this.convertJsonToForm();
            }
        }

    }

    addFormField() {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        const nodeConfig = this.state.nodeConfigs[nodeId];
        if (!nodeConfig || !nodeConfig.config) return;

        // Ensure array exists locally
        if (!nodeConfig.config.formFields) {
            nodeConfig.config.formFields = [];
        }

        // Push the new field
        nodeConfig.config.formFields.push({
            key: '',
            value: ''
        });

        // FIX: Persist the updated array to the workflow state
        this.workflow.updateNodeConfig(nodeId, 'formFields', nodeConfig.config.formFields);

        this.state.configUpdateCounter++;

        setTimeout(() => {
            const formContainer = document.querySelector('.form-fields-container');
            if (formContainer) {
                formContainer.scrollTop = formContainer.scrollHeight;
            }
        }, 100);
    }

    updateFormField(index, fieldType, value) {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        const nodeConfig = this.state.nodeConfigs[nodeId];
        if (nodeConfig.config.formFields && nodeConfig.config.formFields[index]) {
            // Update local object
            nodeConfig.config.formFields[index][fieldType] = value;

            // FIX: Persist changes to workflow state
            this.workflow.updateNodeConfig(nodeId, 'formFields', nodeConfig.config.formFields);

            this.state.configUpdateCounter++;
        }
    }

    removeFormField(index) {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        const nodeConfig = this.state.nodeConfigs[nodeId];
        if (nodeConfig.config.formFields && nodeConfig.config.formFields.length > index) {
            const removedField = nodeConfig.config.formFields.splice(index, 1);

            // FIX: Persist changes to workflow state
            this.workflow.updateNodeConfig(nodeId, 'formFields', nodeConfig.config.formFields);

            this.state.configUpdateCounter++;

            if (nodeConfig.config.formFields.length === 0) {
                setTimeout(() => this.addFormField(), 100);
            }
        }
    }

    clearAllFormFields() {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        if (confirm("Are you sure you want to clear all form fields?")) {
            const nodeConfig = this.state.nodeConfigs[nodeId];
            nodeConfig.config.formFields = [];

            // FIX: Persist changes to workflow state
            this.workflow.updateNodeConfig(nodeId, 'formFields', []);

            this.state.configUpdateCounter++;

            setTimeout(() => this.addFormField(), 100);
        }
    }

    convertFormToJson() {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        const nodeConfig = this.state.nodeConfigs[nodeId];
        if (!nodeConfig.config.formFields || nodeConfig.config.formFields.length === 0) {
            this.notification.add("No form fields to convert", { type: 'warning' });
            return;
        }

        try {
            const jsonObject = {};
            let hasValidFields = false;

            nodeConfig.config.formFields.forEach(field => {
                if (field.key && field.key.trim() !== '') {
                    hasValidFields = true;
                    const key = field.key.trim();
                    let value = field.value;

                    if (value === 'true') value = true;
                    else if (value === 'false') value = false;
                    else if (value === 'null') value = null;
                    else if (!isNaN(value) && value.trim() !== '') value = Number(value);
                    else if (value.trim() === '') value = '';

                    jsonObject[key] = value;
                }
            });

            if (!hasValidFields) {
                this.notification.add("No valid fields to convert", { type: 'warning' });
                return;
            }

            const jsonString = JSON.stringify(jsonObject, null, 2);

            // FIX: Changed 'this.updateNodeConfig' to 'this.workflow.updateNodeConfig'
            this.workflow.updateNodeConfig(nodeId, 'body', jsonString);
            this.workflow.updateNodeConfig(nodeId, 'bodyType', 'json');

            this.notification.add("Form data converted to JSON!", { type: 'success' });
        } catch (error) {
            console.error('❌ FormManager: Error converting form to JSON:', error);
            this.notification.add("Error converting form data", { type: 'danger' });
        }
    }

    convertJsonToForm(nodeId = null) {
        const targetNodeId = nodeId || this.state.selectedNode;
        if (!targetNodeId) {
            console.error('❌ FormManager: No node selected for JSON conversion');
            this.notification.add("No node selected", { type: 'warning' });
            return;
        }

        const nodeConfig = this.state.nodeConfigs[targetNodeId];
        if (!nodeConfig) {
            console.error('❌ FormManager: Node config not found:', targetNodeId);
            return;
        }


        if (!nodeConfig.config.body || nodeConfig.config.body.trim() === '') {
            this.notification.add("No JSON data to convert", { type: 'warning' });
            return;
        }

        try {
            const jsonObject = JSON.parse(nodeConfig.config.body);
            const formFields = [];

            Object.entries(jsonObject).forEach(([key, value]) => {
                formFields.push({
                    key: key,
                    value: typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
                });
            });

            this.workflow.updateNodeConfig(targetNodeId, 'formFields', formFields);

            if (nodeConfig.config.bodyType !== 'form') {
                this.workflow.updateNodeConfig(targetNodeId, 'bodyType', 'form');
            }

            this.notification.add("JSON converted to form data!", { type: 'success' });

            this.state.configUpdateCounter++;

        } catch (error) {
            console.error('❌ FormManager: Error parsing JSON:', error);
            this.notification.add("Invalid JSON format - please check your JSON syntax", { type: 'danger' });
        }
    }

    generateJsonFromForm(formFields) {
        if (!formFields || !Array.isArray(formFields) || formFields.length === 0) {
            return '{}';
        }

        const jsonObject = {};
        let hasValidFields = false;

        formFields.forEach(field => {
            if (field.key && field.key.trim() !== '') {
                hasValidFields = true;
                const key = field.key.trim();
                let value = field.value;

                if (value === 'true') value = true;
                else if (value === 'false') value = false;
                else if (value === 'null') value = null;
                else if (!isNaN(value) && value.trim() !== '') value = Number(value);
                else if (value.trim() === '') value = '';

                jsonObject[key] = value;
            }
        });

        if (!hasValidFields) {
            return '{}';
        }

        return JSON.stringify(jsonObject, null, 2);
    }

    hasFormFields(nodeId) {
        const nodeConfig = this.state.nodeConfigs[nodeId];
        return nodeConfig &&
               nodeConfig.config &&
               nodeConfig.config.formFields &&
               Array.isArray(nodeConfig.config.formFields) &&
               nodeConfig.config.formFields.length > 0;
    }

}