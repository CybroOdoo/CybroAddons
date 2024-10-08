/** @odoo-module **/
import { useState } from "@odoo/owl";
/**
 * NewTools module for managing CSS properties and their options.
 */
const NewTools = {
     /**
     * Contains a list of CSS properties with their details.
     * Each property includes its name, type, options, unit (if applicable), min and max values,
     * and alternative prefixes.
     */
    'property': [
        // List of CSS properties...
        {'name': 'align-content', 'type': 'select', 'options': ['baseline', 'center', 'flex-start', 'flex-end', 'stretch', 'initial', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'align-items', 'type': 'select', 'options': ['baseline', 'center', 'flex-start', 'flex-end', 'stretch', 'initial', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'align-self', 'type': 'select', 'options': ['auto', 'baseline', 'center', 'flex-start', 'flex-end', 'stretch', 'initial', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'animation-delay', 'type': 'range', 'unit': 's', 'min': 0, 'max': 60, 'alt': ['-webkit-']},
        {'name': 'animation-direction', 'type': 'select', 'options': ['normal', 'reverse', 'alternate', 'alternate-reverse', 'initial', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'animation-duration', 'type': 'range', 'unit': 's', 'min': 0, 'max': 60, 'alt': ['-webkit-']},
        {'name': 'animation-fill-mode', 'type': 'select', 'options': ['none', 'forwards', 'backwards', 'both', 'initial', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'animation-iteration-count', 'type': 'range', 'unit': false, 'min': -1, 'max': 10, 'alt': ['-webkit-']},
        {'name': 'animation-name', 'type': 'input', 'alt': ['-webkit-']},
        {'name': 'animation-play-state', 'type': 'select', 'options': ['paused', 'running', 'initial', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'animation-timing-function', 'type': 'select', 'options': ['linear', 'ease', 'ease-in', 'ease-out', 'ease-in-out', 'initial', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'backface-visibility', 'type': 'select', 'options': ['visible', 'hidden', 'initial', 'inherit'], 'alt': []},
        {'name': 'background-attachment', 'type': 'select', 'options': ['scroll', 'fixed', 'inherit'], 'alt': []},
        {'name': 'background-clip', 'type': 'select', 'options': ['border-box', 'padding-box', 'content-box', 'initial', 'inherit'], 'alt': []},
        {'name': 'background-color', 'type': 'color', 'alt': []},
        {'name': 'background-origin', 'type': 'select', 'options': ['border-box', 'padding-box', 'content-box', 'initial', 'inherit'], 'alt': []},
        {'name': 'background-repeat', 'type': 'select', 'options': ['repeat', 'repeat-x ', 'repeat-y', 'no-repeat', 'inherit'], 'alt': []},
        {'name': 'background-size', 'type': 'range', 'unit': '%', 'min': 0, 'max': 100, 'alt': []},
        {'name': 'border', 'type': 'input', 'alt': []},
        {'name': 'border-bottom', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'border-bottom-color', 'type': 'color', 'alt': []},
        {'name': 'border-bottom-left-radius', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 100, 'alt': []},
        {'name': 'border-bottom-right-radius', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 100, 'alt': []},
        {'name': 'border-bottom-style', 'type': 'select', 'options': ['none', 'hidden', 'dotted', 'dashed', 'solid', 'double', 'groove', 'ridge', 'inset', 'outset', 'initial', 'inherit'], 'alt': []},
        {'name': 'border-bottom-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'border-collapse', 'type': 'select', 'options': ['collapse', 'separate', 'inherit'], 'alt': []},
        {'name': 'border-color', 'type': 'color', 'alt': []},
        {'name': 'border-left', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'border-left-color', 'type': 'color', 'alt': []},
        {'name': 'border-left-style', 'type': 'select', 'options': ['none', 'hidden', 'dotted', 'dashed', 'solid', 'double', 'groove', 'ridge', 'inset', 'outset', 'initial', 'inherit'], 'alt': []},
        {'name': 'border-left-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'border-radius', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 100, 'alt': []},
        {'name': 'border-right', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'border-right-color', 'type': 'color', 'alt': []},
        {'name': 'border-right-style', 'type': 'select', 'options': ['none', 'hidden', 'dotted', 'dashed', 'solid', 'double', 'groove', 'ridge', 'inset', 'outset', 'initial', 'inherit'], 'alt': []},
        {'name': 'border-right-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'border-spacing', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'border-style', 'type': 'select', 'options': ['none', 'hidden', 'dotted', 'dashed', 'solid', 'double', 'groove', 'ridge', 'inset', 'outset', 'initial', 'inherit'], 'alt': []},
        {'name': 'border-top', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'border-top-color', 'type': 'color', 'alt': []},
        {'name': 'border-top-left-radius', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 100, 'alt': []},
        {'name': 'border-top-right-radius', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 100, 'alt': []},
        {'name': 'border-top-style', 'type': 'select', 'options': ['none', 'hidden', 'dotted', 'dashed', 'solid', 'double', 'groove', 'ridge', 'inset', 'outset', 'initial', 'inherit'], 'alt': []},
        {'name': 'border-top-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'border-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'bottom', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'box-shadow', 'type': 'input', 'alt': []},
        {'name': 'box-sizing', 'type': 'select', 'options': ['content-box', 'padding-box', 'border-box', 'initial', 'inherit'], 'alt': []},
        {'name': 'caption-side', 'type': 'select', 'options': ['top', 'bottom', 'inherit'], 'alt': []},
        {'name': 'clear', 'type': 'select', 'options': ['none', 'left', 'right', 'both', 'inherit', 'auto'], 'alt': []},
        {'name': 'color', 'type': 'color', 'alt': []},
        {'name': 'column-count', 'type': 'range', 'unit': false, 'min': 0, 'max': 10, 'alt': ['-webkit-', '-moz-']},
        {'name': 'column-fill', 'type': 'select', 'options': ['auto', 'balance', 'initial', 'inherit'], 'alt': ['-webkit-', '-moz-']},
        {'name': 'column-gap', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 25, 'alt': ['-webkit-', '-moz-']},
        {'name': 'column-rule-color', 'type': 'color', 'alt': ['-webkit-', '-moz-']},
        {'name': 'column-rule-style', 'type': 'select', 'options': ['none', 'hidden', 'dotted', 'dashed', 'solid', 'double', 'groove', 'ridge', 'inset', 'outset', 'initial', 'inherit'], 'alt': ['-webkit-', '-moz-']},
        {'name': 'column-rule-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 25, 'alt': ['-webkit-', '-moz-']},
        {'name': 'column-span', 'type': 'select', 'options': ['none', 'all', 'initial', 'inherit'], 'alt': ['-webkit-', '-moz-']},
        {'name': 'column-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': ['-webkit-', '-moz-']},
        {'name': 'cursor', 'type': 'select',
         'options': ['auto', 'crosshair', 'default', 'pointer', 'move', 'e-resize',
                     'ne-resize', 'nw-resize', 'n-resize', 'se-resize', 'sw-resize',
                     's-resize', 'w-resize', 'text', 'wait', 'help', 'progress',
                     'inherit'], 'alt': []},
        {'name': 'direction', 'type': 'select', 'options': ['ltr', 'rtl', 'inherit'], 'alt': []},
        {'name': 'display', 'type': 'select',
         'options': ['flex', 'inline', 'block', 'list-item', 'inline-block', 'table',
                     'inline-table', 'table-row-group', 'table-header-group',
                     'table-footer-group', 'table-row', 'table-column-group',
                     'table-column', 'table-cell', 'table-caption', 'none',
                     'inherit'], 'alt': []},
        {'name': 'empty-cells', 'type': 'select', 'options': ['show', 'hide', 'inherit'], 'alt': []},
        {'name': 'flex', 'type': 'range', 'unit': false, 'min': 0, 'max': 10, 'alt': ['-webkit-', '-ms-']},
        {'name': 'flex-basis', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': ['-webkit-']},
        {'name': 'flex-direction', 'type': 'select', 'options': ['left', 'right', 'none', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'flex-grow', 'type': 'range', 'unit': false, 'min': 0, 'max': 10, 'alt': ['-webkit-']},
        {'name': 'flex-shrink', 'type': 'range', 'unit': false, 'min': 0, 'max': 10, 'alt': ['-webkit-']},
        {'name': 'flex-wrap', 'type': 'select', 'options': ['nowrap', 'wrap', 'wrap-reverse', 'initial', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'float', 'type': 'select', 'options': ['left', 'right', 'none', 'initial', 'inherit'], 'alt': []},
        {'name': 'font-family', 'type': 'input', 'alt': []},
        {'name': 'font-size', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 34, 'alt': []},
        {'name': 'font-size-adjust', 'type': 'range', 'unit': false, 'min': 0, 'max': 10, 'alt': []},
        {'name': 'font-stretch', 'type': 'select', 'options': ['normal', 'ultra-condensed', 'extra-condensed', 'condensed', 'semi-condensed', 'semi-expanded', 'expanded', 'extra-expanded', 'ultra-expanded', 'initial', 'inherit'], 'alt': []},
        {'name': 'font-style', 'type': 'select', 'options': ['normal', 'italic', 'oblique', 'inherit'], 'alt': []},
        {'name': 'font-variant', 'type': 'select', 'options': ['normal', 'small-caps', 'inherit'], 'alt': []},
        {'name': 'font-weight', 'type': 'select', 'options': ['normal', 'bold', 'bolder', 'lighter', '100', '200', '300', '400', '500', '600', '700', '800', '900', 'inherit'], 'alt': []},
        {'name': 'height', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'justify-content', 'type': 'select', 'options': ['flex-start', 'flex-end', 'center', 'space-between', 'space-around', 'initial', 'inherit'],  'alt': ['-webkit-']},
        {'name': 'left', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'letter-spacing', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'line-height', 'type': 'range', 'unit': false, 'min': 0, 'max': 10, 'alt': []},
        {'name': 'list-style-position', 'type': 'select', 'options': ['inside', 'outside', 'initial', 'inherit'], 'alt': []},
        {'name': 'list-style-type', 'type': 'select', 'options': ['disc', 'circle', 'square', 'decimal', 'decimal-leading-zero', 'lower-roman', 'upper-roman', 'lower-greek', 'lower-latin', 'upper-latin', 'armenian', 'georgian', 'lower-alpha', 'upper-alpha', 'none', 'inherit'], 'alt': []},
        {'name': 'margin', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'margin-bottom', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'margin-left', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'margin-right', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'margin-top', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'max-height', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'max-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'min-height', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'min-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'opacity', 'type': 'range', 'unit': '%', 'min': 0, 'max': 100, 'alt': []},
        {'name': 'order', 'type': 'range', 'unit': false, 'min': 0, 'max': 10,  'alt': ['-webkit-']},
        {'name': 'outline-color', 'type': 'color', 'alt': []},
        {'name': 'outline-offset', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'outline-style', 'type': 'select', 'options': ['none', 'dotted', 'dashed', 'solid', 'double', 'groove', 'ridge', 'inset', 'outset', 'initial', 'inherit'], 'alt': []},
        {'name': 'outline-width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 25, 'alt': []},
        {'name': 'overflow', 'type': 'select', 'options': ['visible', 'hidden', 'scroll', 'auto', 'inherit'], 'alt': []},
        {'name': 'overflow-x', 'type': 'select', 'options': ['visible', 'hidden', 'scroll', 'auto', 'inherit'], 'alt': []},
        {'name': 'overflow-y', 'type': 'select', 'options': ['visible', 'hidden', 'scroll', 'auto', 'inherit'], 'alt': []},
        {'name': 'padding', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'padding-bottom', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'padding-left', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'padding-right', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'padding-top', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'page-break-after', 'type': 'select', 'options': ['auto', 'always', 'avoid', 'left', 'right', 'inherit'], 'alt': []},
        {'name': 'page-break-before', 'type': 'select', 'options': ['auto', 'always', 'avoid', 'left', 'right', 'inherit'], 'alt': []},
        {'name': 'page-break-inside', 'type': 'select', 'options': ['avoid', 'auto', 'inherit'], 'alt': []},
        {'name': 'perspective', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 25, 'alt': []},
        {'name': 'perspective-origin', 'type': 'input', 'alt': []},
        {'name': 'position', 'type': 'select', 'options': ['static', 'relative', 'absolute', 'fixed', 'inherit'], 'alt': []},
        {'name': 'quotes', 'type': 'input', 'alt': []},
        {'name': 'resize', 'type': 'select', 'options': ['none', 'both', 'horizontal', 'vertical', 'initial', 'inherit'], 'alt': []},
        {'name': 'right', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'table-layout', 'type': 'select', 'options': ['auto', 'fixed', 'inherit'], 'alt': []},
        {'name': 'text-align', 'type': 'select', 'options': ['left', 'right', 'center', 'justify', 'inherit']},
        {'name': 'text-align-last', 'type': 'select', 'options': ['left', 'right', 'center', 'justify', 'inherit'], 'alt': ['-moz-']},
        {'name': 'text-decoration-color', 'type': 'color', 'alt': ['-moz-']},
        {'name': 'text-decoration-line', 'type': 'input', 'alt': ['-moz-']},
        {'name': 'text-decoration-style', 'type': 'select', 'options': ['none', 'underline', 'overline', 'line-through', 'blink', 'inherit'], 'alt': ['-moz-']},
        {'name': 'text-indent', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 20, 'alt': []},
        {'name': 'text-justify', 'type': 'select', 'options': ['auto', 'none', 'inter-word', 'distribute', 'initial', 'inherit'], 'alt': []},
        {'name': 'text-overflow', 'type': 'select', 'options': ['clip', 'ellipsis', 'string', 'initial', 'inherit'], 'alt': []},
        {'name': 'text-shadow', 'type': 'input', 'alt': []},
        {'name': 'text-transform', 'type': 'select', 'options': ['capitalize', 'uppercase', 'lowercase', 'none', 'inherit'], 'alt': []},
        {'name': 'top', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'transform', 'type': 'input', 'alt': ['-webkit-', '-moz-', '-ms-']},
        {'name': 'transform-origin', 'type': 'select', 'options': ['x-position', 'y-position', 'z-position', 'initial', 'inherit'], 'alt': ['-webkit-', '-moz-', '-ms-']},
        {'name': 'transform-style', 'type': 'select', 'options': ['flat', 'preserve-3d', 'initial', 'inherit'], 'alt': ['-webkit-', '-moz-', '-ms-']},
        {'name': 'transition', 'type': 'input', 'alt': ['-webkit-']},
        {'name': 'transition-delay', 'type': 'range', 'unit': 's', 'min': 0, 'max': 60, 'alt': ['-webkit-']},
        {'name': 'transition-duration', 'type': 'range', 'unit': 's', 'min': 0, 'max': 60, 'alt': ['-webkit-']},
        {'name': 'transition-property', 'type': 'input', 'alt': ['-webkit-']},
        {'name': 'transition-timing-function', 'type': 'select', 'options': ['linear', 'ease', 'ease-in', 'ease-out', 'ease-in-out', 'initial', 'inherit'], 'alt': ['-webkit-']},
        {'name': 'visibility', 'type': 'select', 'options': ['visible', 'hidden', 'collapse', 'inherit'], 'alt': []},
        {'name': 'white-space', 'type': 'select', 'options': ['normal', 'pre', 'nowrap', 'pre-wrap', 'pre-line', 'inherit'], 'alt': []},
        {'name': 'width', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 500, 'alt': []},
        {'name': 'word-break', 'type': 'select', 'options': ['normal', 'break-all', 'keep - all', 'initial', 'inherit'], 'alt': []},
        {'name': 'word-spacing', 'type': 'range', 'unit': 'px', 'min': 0, 'max': 10, 'alt': []},
        {'name': 'word-wrap', 'type': 'select', 'options': ['normal', 'break-word', 'initial', 'inherit'], 'alt': []},
    ]
}
/**
 * Capitalizes and formats the given string to display as property name.
 * @param {string} name - The property name.
 * @returns {string} The formatted property name.
 */
function displayName(nme){
    let names = nme.split('-');
    let newName = '';
    for(let name of names){
        if(newName == ''){
            newName += name.charAt(0).toUpperCase() + name.slice(1);
        } else {
            newName += ' ' + name.charAt(0).toUpperCase() + name.slice(1);
        }
    }
    return newName;
}

for(let tool of NewTools.property){
    tool.displayName = displayName(tool.name)
}

export { NewTools };
