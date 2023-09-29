/** @odoo-module **/
/**
     * This file is used to create the domain as tree structure based on the
         branch and node domains and also based on the operator.
*/
import { Domain } from "@web/core/domain";
import { formatAST, toPyValue} from "@web/core/py_js/py_utils";
const TERM_OPERATORS_NEGATION = {
    "<": ">=",
    ">": "<=",
    "<=": ">",
    ">=": "<",
    "=": "!=",
    "!=": "=",
    in: "not in",
    like: "not like",
    ilike: "not ilike",
    "not in": "in",
    "not like": "like",
    "not ilike": "ilike",
};

function _construcTree(ASTs, distributeNot, negate = false) {
    // Construct a tree structure based on the branch and node domains and the operator.
    const [firstAST, ...tailASTs] = ASTs;

    if (firstAST.type === 1 && firstAST.value === "!") {
        return _construcTree(tailASTs, distributeNot, !negate);
    }

    const tree = {
        type: firstAST.type === 1 ? "connector" : "condition"
    };
    if (tree.type === "connector") {
        tree.value = firstAST.value;
        if (distributeNot && negate) {
            tree.value = tree.value === "&" ? "|" : "&";
            tree.negate = false;
        } else {
            tree.negate = negate;
        }
        tree.children = [];
    } else {
        const [pathAST, operatorAST, valueAST] = firstAST.value;
        tree.path = pathAST.value;
        if (negate && TERM_OPERATORS_NEGATION[operatorAST.value]) {
            tree.operator = TERM_OPERATORS_NEGATION[operatorAST.value];
        } else {
            tree.operator = operatorAST.value;
            tree.negate = negate;
        }
        tree.valueAST = valueAST;
    }
    let remaimingASTs = tailASTs;
    if (tree.type === "connector") {
        for (let i = 0; i < 2; i++) {
            const {
                tree: child,
                remaimingASTs: otherASTs
            } = _construcTree(
                remaimingASTs,
                distributeNot,
                distributeNot && negate
            );
            remaimingASTs = otherASTs;
            if (child.type === "connector" && !child.negate && child.value === tree.value) {
                tree.children.push(...child.children);
            } else {
                tree.children.push(child);
            }
        }
    }
    return {
        tree,
        remaimingASTs
    };
}

function construcTree(initialASTs, options) {
    // Construct a tree structure based on the initial abstract syntax trees and options
    const value = options.defaultConnector || "&";
    if (!initialASTs.length) {
        return {
            type: "connector",
            value,
            negate: false,
            children: []
        };
    }
    const {
        tree
    } = _construcTree(initialASTs, options.distributeNot);
    if (tree.type === "condition") {
        return {
            type: "connector",
            value,
            negate: false,
            children: [tree]
        };
    }
    return tree;
}

function createBetweenOperators(tree, isRoot = true) {
    // Create between operators from a tree structure representing the domain.
    if (tree.type === "condition") {
        return tree;
    }
    const processedChildren = tree.children.map((c) => createBetweenOperators(c, false));
    if (tree.value === "|") {
        return {
            ...tree,
            children: processedChildren
        };
    }
    const children = [];
    for (let i = 0; i < processedChildren.length; i++) {
        const child1 = processedChildren[i];
        const child2 = processedChildren[i + 1];
        if (
            child1.type === "condition" &&
            child2 &&
            child2.type === "condition" &&
            child1.path === child2.path &&
            child1.operator === ">=" &&
            child2.operator === "<="
        ) {
            children.push({
                type: "condition",
                path: child1.path,
                operator: "between",
                valueAST: {
                    type: 4,
                    value: [child1.valueAST, child2.valueAST],
                },
            });
            i += 1;
        } else {
            children.push(child1);
        }
    }
    if (children.length === 1 && !isRoot) {
        return {
            ...children[0]
        };
    }
    return {
        ...tree,
        children
    };
}

export function toTree(domain, options = {}) {
    // Convert a domain to a tree structure.
    domain = new Domain(domain);
    const domainAST = domain.ast;
    const tree = construcTree(domainAST.value, options);
    return createBetweenOperators(tree);
}
