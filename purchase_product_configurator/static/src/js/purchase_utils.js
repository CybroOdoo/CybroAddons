/**
 * Get the selected custom PTAV in the provided PTAL, if any.
 *
 * Note: a PTAL can have at most one selected custom PTAV, by design.
 *
 * @param {ProductTemplateAttributeLine.props} ptal The PTAL in which to look for the selected
 *     custom PTAV.
 * @return {Object|undefined} The selected custom PTAV, if any.
 *
 */
export function getSelectedCustomPtav(ptal) {
    const selectedPtavIds = new Set(ptal.selected_attribute_value_ids);
    return ptal.attribute_values.find(ptav => ptav.is_custom && selectedPtavIds.has(ptav.id));
}
