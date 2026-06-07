from __future__ import annotations

import re
from functools import lru_cache
from itertools import product
from typing import Iterator


Tree = tuple


def normalize_op_to_diamond(text: str) -> str:
    return text.replace("*", "◇")


def parse_variables(text: str) -> list[str]:
    seen: set[str] = set()
    variables: list[str] = []
    for variable in re.findall(r"\b([a-z])\b", text):
        if variable not in seen:
            seen.add(variable)
            variables.append(variable)
    return variables


def split_equation(equation: str) -> tuple[str, str] | None:
    parts = normalize_op_to_diamond(equation).split("=", 1)
    if len(parts) != 2:
        return None
    return parts[0].strip(), parts[1].strip()


def has_mul_roots(equation: str) -> bool:
    sides = split_equation(equation)
    if sides is None:
        return False
    try:
        return all(parse_op_tree(side)[0] == "op" for side in sides)
    except Exception:
        return False


def has_source_constancy_variable(equation: str) -> bool:
    sides = split_equation(equation)
    if sides is None:
        return False
    lhs_vars = set(re.findall(r"\b([a-z])\b", sides[0]))
    rhs_vars = set(re.findall(r"\b([a-z])\b", sides[1]))
    return bool(lhs_vars - rhs_vars or rhs_vars - lhs_vars)


def parse_op_tree(text: str) -> Tree:
    text = normalize_op_to_diamond(text).strip()
    while len(text) >= 2 and text[0] == "(" and text[-1] == ")":
        depth = 0
        matched = True
        for index, char in enumerate(text):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            if depth == 0 and index < len(text) - 1:
                matched = False
                break
        if not matched:
            break
        text = text[1:-1].strip()

    depth = 0
    last_op = -1
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "◇" and depth == 0:
            last_op = index
    if last_op >= 0:
        return ("op", parse_op_tree(text[:last_op]), parse_op_tree(text[last_op + 1 :]))
    return ("var", text.strip())


def tree_to_str(tree: Tree) -> str:
    if tree[0] == "var":
        return tree[1]
    return f"({tree_to_str(tree[1])} ◇ {tree_to_str(tree[2])})"


def unify_tree(
    template: Tree,
    target: Tree,
    template_vars: set[str],
    subst: dict[str, str] | None = None,
) -> dict[str, str] | None:
    if subst is None:
        subst = {}
    if template[0] == "var" and template[1] in template_vars:
        variable = template[1]
        target_text = tree_to_str(target)
        if variable in subst:
            return subst if subst[variable] == target_text else None
        subst[variable] = target_text
        return subst
    if template[0] == "var" and target[0] == "var":
        return subst if template[1] == target[1] else None
    if template[0] == "op" and target[0] == "op":
        left_subst = unify_tree(template[1], target[1], template_vars, subst)
        if left_subst is None:
            return None
        return unify_tree(template[2], target[2], template_vars, left_subst)
    return None


def get_subtree(tree: Tree, path: str) -> Tree:
    if not path or tree[0] != "op":
        return tree
    return get_subtree(tree[1] if path[0] == "L" else tree[2], path[1:])


def apply_rewrite_at(tree: Tree, path: str, new_subtree: Tree) -> Tree:
    if not path:
        return new_subtree
    if tree[0] != "op":
        return tree
    if path[0] == "L":
        return ("op", apply_rewrite_at(tree[1], path[1:], new_subtree), tree[2])
    return ("op", tree[1], apply_rewrite_at(tree[2], path[1:], new_subtree))


def wrap_congr_arg(tree: Tree, path: str, inner_proof: str) -> str:
    if not path or tree[0] != "op":
        return inner_proof
    if path[0] == "L":
        subproof = wrap_congr_arg(tree[1], path[1:], inner_proof)
        shared = tree_to_str(tree[2])
        return f"congrArg (· ◇ {shared}) ({subproof})"
    subproof = wrap_congr_arg(tree[2], path[1:], inner_proof)
    shared = tree_to_str(tree[1])
    return f"congrArg ({shared} ◇ ·) ({subproof})"


def build_constancy_info(
    source_equation: str,
    source_vars: list[str],
    target_vars: list[str],
) -> tuple[list[dict], set[str], set[str]]:
    parts = normalize_op_to_diamond(source_equation).split("=", 1)
    if len(parts) != 2:
        return [], set(), set()
    source_lhs = parts[0].strip()
    source_rhs = parts[1].strip()
    lhs_vars = set(re.findall(r"\b([a-z])\b", source_lhs))
    rhs_vars = set(re.findall(r"\b([a-z])\b", source_rhs))
    lhs_only = lhs_vars - rhs_vars
    rhs_only = rhs_vars - lhs_vars
    constancy_info: list[dict] = []

    used = set(source_vars) | set(target_vars)
    fresh_vars = [char for char in "abcdefghijklmnopqrstuvwxyz" if char not in used]
    if len(fresh_vars) < 2:
        return [], lhs_only, rhs_only

    for free_var in sorted(rhs_only):
        pos = source_vars.index(free_var) if free_var in source_vars else -1
        if pos < 0:
            continue
        fresh_a, fresh_b = fresh_vars[:2]
        args_a = list(source_vars)
        args_b = list(source_vars)
        args_a[pos] = fresh_a
        args_b[pos] = fresh_b
        rhs_a = re.sub(r"\b" + free_var + r"\b", fresh_a, source_rhs)
        rhs_b = re.sub(r"\b" + free_var + r"\b", fresh_b, source_rhs)
        other_vars = [var for index, var in enumerate(source_vars) if index != pos]
        quant_vars = other_vars + [fresh_a, fresh_b]
        lemma_proof = f"(h {' '.join(args_a)}).symm.trans (h {' '.join(args_b)})"
        constancy_info.append(
            {
                "have_line": (
                    f"have hconst : ∀ ({' '.join(quant_vars)} : G), "
                    f"{rhs_a} = {rhs_b} := "
                    f"fun {' '.join(quant_vars)} => {lemma_proof}"
                ),
                "lhs_template": rhs_a,
                "rhs_template": rhs_b,
                "lhs_tree": parse_op_tree(rhs_a),
                "rhs_tree": parse_op_tree(rhs_b),
                "tvars": set(quant_vars),
                "quant_vars": quant_vars,
            }
        )

    for free_var in sorted(lhs_only):
        pos = source_vars.index(free_var) if free_var in source_vars else -1
        if pos < 0:
            continue
        fresh_a, fresh_b = fresh_vars[:2]
        args_a = list(source_vars)
        args_b = list(source_vars)
        args_a[pos] = fresh_a
        args_b[pos] = fresh_b
        lhs_a = re.sub(r"\b" + free_var + r"\b", fresh_a, source_lhs)
        lhs_b = re.sub(r"\b" + free_var + r"\b", fresh_b, source_lhs)
        other_vars = [var for index, var in enumerate(source_vars) if index != pos]
        quant_vars = other_vars + [fresh_a, fresh_b]
        lemma_proof = f"(h {' '.join(args_a)}).trans (h {' '.join(args_b)}).symm"
        constancy_info.append(
            {
                "have_line": (
                    f"have hconst : ∀ ({' '.join(quant_vars)} : G), "
                    f"{lhs_a} = {lhs_b} := "
                    f"fun {' '.join(quant_vars)} => {lemma_proof}"
                ),
                "lhs_template": lhs_a,
                "rhs_template": lhs_b,
                "lhs_tree": parse_op_tree(lhs_a),
                "rhs_tree": parse_op_tree(lhs_b),
                "tvars": set(quant_vars),
                "quant_vars": quant_vars,
            }
        )
    return constancy_info, lhs_only, rhs_only


def simultaneous_subst(text: str, variables: list[str], combo: list[str] | tuple[str, ...]) -> str:
    result = normalize_op_to_diamond(text)
    placeholders: list[str] = []
    for index, variable in enumerate(variables):
        placeholder = f"__PH{index}__"
        placeholders.append(placeholder)
        result = re.sub(r"\b" + variable + r"\b", placeholder, result)
    for placeholder, replacement in zip(placeholders, combo):
        result = result.replace(placeholder, replacement)
    return result


def try_constancy_at(
    subtree_a: Tree,
    subtree_b: Tree,
    constancy_info: dict,
    default_fill: str,
) -> str | None:
    lhs_tree = constancy_info.get("lhs_tree") or parse_op_tree(
        constancy_info["lhs_template"]
    )
    rhs_tree = constancy_info.get("rhs_tree") or parse_op_tree(
        constancy_info["rhs_template"]
    )
    template_vars = constancy_info["tvars"]
    subst = unify_tree(lhs_tree, subtree_a, template_vars)
    if subst is not None:
        subst2 = unify_tree(rhs_tree, subtree_b, template_vars, dict(subst))
        if subst2 is not None:
            for variable in constancy_info["quant_vars"]:
                subst2.setdefault(variable, default_fill)
            return " ".join(subst2[variable] for variable in constancy_info["quant_vars"])
    subst = unify_tree(rhs_tree, subtree_a, template_vars)
    if subst is not None:
        subst2 = unify_tree(lhs_tree, subtree_b, template_vars, dict(subst))
        if subst2 is not None:
            for variable in constancy_info["quant_vars"]:
                subst2.setdefault(variable, default_fill)
            args = " ".join(subst2[variable] for variable in constancy_info["quant_vars"])
            return args + "|symm"
    return None


def find_constancy_step(
    tree_a: Tree,
    tree_b: Tree,
    constancy_info: list[dict],
    default_fill: str,
    path_prefix: str = "",
) -> tuple[str, str, bool, int] | None:
    if tree_a == tree_b:
        return None
    for index, info in enumerate(constancy_info):
        result = try_constancy_at(tree_a, tree_b, info, default_fill)
        if result is not None:
            symm = result.endswith("|symm")
            return path_prefix, result.replace("|symm", ""), symm, index
    if tree_a[0] == "op" and tree_b[0] == "op":
        if tree_a[1] != tree_b[1]:
            left = find_constancy_step(
                tree_a[1], tree_b[1], constancy_info, default_fill, path_prefix + "L"
            )
            if left is not None:
                return left
        if tree_a[2] != tree_b[2]:
            right = find_constancy_step(
                tree_a[2], tree_b[2], constancy_info, default_fill, path_prefix + "R"
            )
            if right is not None:
                return right
    return None


def find_constancy_steps(
    start_tree: Tree,
    goal_tree: Tree,
    constancy_info: list[dict],
    default_fill: str,
    max_steps: int = 4,
) -> list[tuple[str, str, bool, int]]:
    steps: list[tuple[str, str, bool, int]] = []
    current = start_tree
    for _ in range(max_steps):
        if current == goal_tree:
            break
        step = find_constancy_step(current, goal_tree, constancy_info, default_fill)
        if step is None:
            return []
        steps.append(step)
        current = apply_rewrite_at(current, step[0], get_subtree(goal_tree, step[0]))
    return steps if current == goal_tree else []


def _constancy_have_lines(
    steps: list[tuple[str, str, bool, int]],
    constancy_info: list[dict],
) -> tuple[list[str], dict[int, str]]:
    used: dict[int, str] = {}
    have_lines: list[str] = []
    for _, _, _, index in steps:
        if index in used:
            continue
        name = "hconst" if not used else f"hconst{len(used) + 1}"
        line = str(constancy_info[index]["have_line"])
        if name != "hconst":
            line = line.replace("hconst", name, 1)
        have_lines.append(line)
        used[index] = name
    return have_lines, used


def _denormalize(normalized_expr: str) -> str | None:
    expr = normalized_expr.replace("◇", " ◇ ")
    try:
        parse_op_tree(expr)
    except Exception:
        return None
    return expr


@lru_cache(maxsize=500_000)
def _tree_from_normalized_expr(normalized_expr: str) -> Tree | None:
    expr = _denormalize(normalized_expr)
    if expr is None:
        return None
    return parse_op_tree(expr)


@lru_cache(maxsize=200_000)
def _parse_hconst_target(
    target_equation: str,
) -> tuple[str, str, str, str, tuple[str, ...], Tree, Tree] | None:
    target_equation = normalize_op_to_diamond(target_equation)
    target_parts = target_equation.split("=", 1)
    if len(target_parts) != 2:
        return None
    target_lhs = target_parts[0].strip()
    target_rhs = target_parts[1].strip()
    target_vars = tuple(parse_variables(target_equation))
    if not target_vars:
        return None
    return (
        target_lhs,
        target_rhs,
        target_lhs.replace(" ", ""),
        target_rhs.replace(" ", ""),
        target_vars,
        parse_op_tree(target_lhs),
        parse_op_tree(target_rhs),
    )


def _h_instantiations(
    source_lhs: str,
    source_rhs: str,
    source_vars: list[str],
    target_vars: list[str],
) -> dict[str, dict[str, str]]:
    h_insts: dict[str, dict[str, str]] = {}

    def add(combo: list[str] | tuple[str, ...]) -> None:
        new_lhs = simultaneous_subst(source_lhs, source_vars, combo)
        new_rhs = simultaneous_subst(source_rhs, source_vars, combo)
        lhs_norm = new_lhs.replace(" ", "")
        rhs_norm = new_rhs.replace(" ", "")
        if lhs_norm == rhs_norm:
            return
        args = " ".join(combo)
        h_insts.setdefault(lhs_norm, {}).setdefault(rhs_norm, args)
        h_insts.setdefault(rhs_norm, {}).setdefault(lhs_norm, args + "|symm")

    for combo in product(target_vars, repeat=len(source_vars)):
        add(combo)

    compound_terms = [f"({left} ◇ {right})" for left in target_vars for right in target_vars]
    count = len(source_vars) * len(compound_terms) * (
        len(target_vars) ** max(len(source_vars) - 1, 0)
    )
    if count <= 50000:
        for position in range(len(source_vars)):
            for term in compound_terms:
                for bare_combo in product(target_vars, repeat=len(source_vars) - 1):
                    combo = list(bare_combo[:position]) + [term] + list(
                        bare_combo[position:]
                    )
                    add(combo)
    return h_insts


def _subterm_texts(tree: Tree) -> tuple[str, ...]:
    seen: set[str] = set()
    terms: list[str] = []

    def visit(node: Tree) -> None:
        text = tree_to_str(node)
        if text not in seen:
            seen.add(text)
            terms.append(text)
        if node[0] == "op":
            visit(node[1])
            visit(node[2])

    visit(tree)
    return tuple(terms)


def _target_terms_for_deep_hinst(
    target_lhs_tree: Tree,
    target_rhs_tree: Tree,
    target_vars: tuple[str, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    terms: list[str] = []
    for term in [*target_vars, *_subterm_texts(target_lhs_tree), *_subterm_texts(target_rhs_tree)]:
        if term not in seen:
            seen.add(term)
            terms.append(term)
    return tuple(terms)


@lru_cache(maxsize=200_000)
def _h_instantiations_for_terms(
    source_lhs: str,
    source_rhs: str,
    source_vars_tuple: tuple[str, ...],
    terms_tuple: tuple[str, ...],
    max_instantiations: int,
) -> dict[str, dict[str, str]] | None:
    source_vars = list(source_vars_tuple)
    terms = list(terms_tuple)
    if not source_vars or not terms:
        return None
    if len(terms) ** len(source_vars) > max_instantiations:
        return None
    h_insts: dict[str, dict[str, str]] = {}

    def add(combo: list[str] | tuple[str, ...]) -> None:
        new_lhs = simultaneous_subst(source_lhs, source_vars, combo)
        new_rhs = simultaneous_subst(source_rhs, source_vars, combo)
        lhs_norm = new_lhs.replace(" ", "")
        rhs_norm = new_rhs.replace(" ", "")
        if lhs_norm == rhs_norm:
            return
        args = " ".join(combo)
        h_insts.setdefault(lhs_norm, {}).setdefault(rhs_norm, args)
        h_insts.setdefault(rhs_norm, {}).setdefault(lhs_norm, args + "|symm")

    for combo in product(terms, repeat=len(source_vars)):
        add(combo)
    return h_insts


@lru_cache(maxsize=200_000)
def _compile_hconst_source_for_target_vars(
    source_equation: str,
    target_vars_tuple: tuple[str, ...],
) -> tuple[str, str, list[str], list[dict], dict[str, dict[str, str]]] | None:
    source_parts = normalize_op_to_diamond(source_equation).split("=", 1)
    if len(source_parts) != 2:
        return None
    source_lhs = source_parts[0].strip()
    source_rhs = source_parts[1].strip()
    source_vars = parse_variables(source_equation)
    target_vars = list(target_vars_tuple)
    if not source_vars or not target_vars:
        return None
    constancy_info, _, _ = build_constancy_info(
        source_equation, source_vars, target_vars
    )
    if not constancy_info:
        return None
    h_insts = _h_instantiations(source_lhs, source_rhs, source_vars, target_vars)
    return source_lhs, source_rhs, source_vars, constancy_info, h_insts


def _h_proof_from_args(args: str) -> str:
    symm = args.endswith("|symm")
    h_args = args.replace("|symm", "")
    return f"(h {h_args}).symm" if symm else f"h {h_args}"


def _subst_tree(tree: Tree, subst: dict[str, str]) -> Tree | None:
    if tree[0] == "var":
        replacement = subst.get(tree[1])
        if replacement is None:
            return None
        return parse_op_tree(replacement)
    left = _subst_tree(tree[1], subst)
    right = _subst_tree(tree[2], subst)
    if left is None or right is None:
        return None
    return ("op", left, right)


def _fill_source_substs(
    partial: dict[str, str],
    source_vars: list[str],
    terms: tuple[str, ...],
    max_instantiations: int,
) -> Iterator[dict[str, str]]:
    missing = [variable for variable in source_vars if variable not in partial]
    if not missing:
        yield dict(partial)
        return
    if len(terms) ** len(missing) > max_instantiations:
        return
    for combo in product(terms, repeat=len(missing)):
        subst = dict(partial)
        subst.update(zip(missing, combo))
        yield subst


def _h_edges_from_target_expr(
    *,
    target_tree: Tree,
    source_lhs_tree: Tree,
    source_rhs_tree: Tree,
    source_vars: list[str],
    source_var_set: set[str],
    terms: tuple[str, ...],
    max_instantiations: int,
) -> Iterator[tuple[Tree, str]]:
    lhs_subst = unify_tree(source_lhs_tree, target_tree, source_var_set)
    if lhs_subst is not None:
        for subst in _fill_source_substs(
            lhs_subst,
            source_vars,
            terms,
            max_instantiations,
        ):
            intermediate = _subst_tree(source_rhs_tree, subst)
            if intermediate is not None:
                yield intermediate, " ".join(subst[variable] for variable in source_vars)

    rhs_subst = unify_tree(source_rhs_tree, target_tree, source_var_set)
    if rhs_subst is not None:
        for subst in _fill_source_substs(
            rhs_subst,
            source_vars,
            terms,
            max_instantiations,
        ):
            intermediate = _subst_tree(source_lhs_tree, subst)
            if intermediate is not None:
                yield (
                    intermediate,
                    " ".join(subst[variable] for variable in source_vars) + "|symm",
                )


def _default_filled_subst(
    partial: dict[str, str],
    source_vars: list[str],
    default_fill: str,
) -> dict[str, str]:
    subst = dict(partial)
    for variable in source_vars:
        subst.setdefault(variable, default_fill)
    return subst


def _h_edges_from_target_expr_default_fill(
    *,
    target_tree: Tree,
    source_lhs_tree: Tree,
    source_rhs_tree: Tree,
    source_vars: list[str],
    source_var_set: set[str],
    default_fill: str,
) -> Iterator[tuple[Tree, str]]:
    lhs_subst = unify_tree(source_lhs_tree, target_tree, source_var_set)
    if lhs_subst is not None:
        subst = _default_filled_subst(lhs_subst, source_vars, default_fill)
        intermediate = _subst_tree(source_rhs_tree, subst)
        if intermediate is not None:
            yield intermediate, " ".join(subst[variable] for variable in source_vars)

    rhs_subst = unify_tree(source_rhs_tree, target_tree, source_var_set)
    if rhs_subst is not None:
        subst = _default_filled_subst(rhs_subst, source_vars, default_fill)
        intermediate = _subst_tree(source_lhs_tree, subst)
        if intermediate is not None:
            yield (
                intermediate,
                " ".join(subst[variable] for variable in source_vars) + "|symm",
            )


def _h_preimage_edges_to_target_expr_default_fill(
    *,
    target_tree: Tree,
    source_lhs_tree: Tree,
    source_rhs_tree: Tree,
    source_vars: list[str],
    source_var_set: set[str],
    default_fill: str,
) -> Iterator[tuple[Tree, str]]:
    rhs_subst = unify_tree(source_rhs_tree, target_tree, source_var_set)
    if rhs_subst is not None:
        subst = _default_filled_subst(rhs_subst, source_vars, default_fill)
        intermediate = _subst_tree(source_lhs_tree, subst)
        if intermediate is not None:
            yield intermediate, " ".join(subst[variable] for variable in source_vars)

    lhs_subst = unify_tree(source_lhs_tree, target_tree, source_var_set)
    if lhs_subst is not None:
        subst = _default_filled_subst(lhs_subst, source_vars, default_fill)
        intermediate = _subst_tree(source_rhs_tree, subst)
        if intermediate is not None:
            yield (
                intermediate,
                " ".join(subst[variable] for variable in source_vars) + "|symm",
            )


def _h_edges_from_target_expr_term_fill(
    *,
    target_tree: Tree,
    source_lhs_tree: Tree,
    source_rhs_tree: Tree,
    source_vars: list[str],
    source_var_set: set[str],
    terms: tuple[str, ...],
    max_instantiations: int,
) -> Iterator[tuple[Tree, str]]:
    lhs_subst = unify_tree(source_lhs_tree, target_tree, source_var_set)
    if lhs_subst is not None:
        for subst in _fill_source_substs(
            lhs_subst,
            source_vars,
            terms,
            max_instantiations,
        ):
            intermediate = _subst_tree(source_rhs_tree, subst)
            if intermediate is not None:
                yield intermediate, " ".join(subst[variable] for variable in source_vars)

    rhs_subst = unify_tree(source_rhs_tree, target_tree, source_var_set)
    if rhs_subst is not None:
        for subst in _fill_source_substs(
            rhs_subst,
            source_vars,
            terms,
            max_instantiations,
        ):
            intermediate = _subst_tree(source_lhs_tree, subst)
            if intermediate is not None:
                yield (
                    intermediate,
                    " ".join(subst[variable] for variable in source_vars) + "|symm",
                )


def _h_preimage_edges_to_target_expr_term_fill(
    *,
    target_tree: Tree,
    source_lhs_tree: Tree,
    source_rhs_tree: Tree,
    source_vars: list[str],
    source_var_set: set[str],
    terms: tuple[str, ...],
    max_instantiations: int,
) -> Iterator[tuple[Tree, str]]:
    rhs_subst = unify_tree(source_rhs_tree, target_tree, source_var_set)
    if rhs_subst is not None:
        for subst in _fill_source_substs(
            rhs_subst,
            source_vars,
            terms,
            max_instantiations,
        ):
            intermediate = _subst_tree(source_lhs_tree, subst)
            if intermediate is not None:
                yield intermediate, " ".join(subst[variable] for variable in source_vars)

    lhs_subst = unify_tree(source_lhs_tree, target_tree, source_var_set)
    if lhs_subst is not None:
        for subst in _fill_source_substs(
            lhs_subst,
            source_vars,
            terms,
            max_instantiations,
        ):
            intermediate = _subst_tree(source_rhs_tree, subst)
            if intermediate is not None:
                yield (
                    intermediate,
                    " ".join(subst[variable] for variable in source_vars) + "|symm",
                )


def _h_preimage_edges_to_target_expr(
    *,
    target_tree: Tree,
    source_lhs_tree: Tree,
    source_rhs_tree: Tree,
    source_vars: list[str],
    source_var_set: set[str],
    terms: tuple[str, ...],
    max_instantiations: int,
) -> Iterator[tuple[Tree, str]]:
    rhs_subst = unify_tree(source_rhs_tree, target_tree, source_var_set)
    if rhs_subst is not None:
        for subst in _fill_source_substs(
            rhs_subst,
            source_vars,
            terms,
            max_instantiations,
        ):
            intermediate = _subst_tree(source_lhs_tree, subst)
            if intermediate is not None:
                yield intermediate, " ".join(subst[variable] for variable in source_vars)

    lhs_subst = unify_tree(source_lhs_tree, target_tree, source_var_set)
    if lhs_subst is not None:
        for subst in _fill_source_substs(
            lhs_subst,
            source_vars,
            terms,
            max_instantiations,
        ):
            intermediate = _subst_tree(source_rhs_tree, subst)
            if intermediate is not None:
                yield (
                    intermediate,
                    " ".join(subst[variable] for variable in source_vars) + "|symm",
                )


def iter_hconst_match_collapse_proof_bodies(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
) -> Iterator[str]:
    source_equation = normalize_op_to_diamond(source_equation)
    target = _parse_hconst_target(target_equation)
    if target is None:
        return
    (
        target_lhs,
        target_rhs,
        target_lhs_norm,
        target_rhs_norm,
        target_vars_tuple,
        target_lhs_tree,
        target_rhs_tree,
    ) = target

    compiled = _compile_hconst_source_for_target_vars(
        source_equation,
        target_vars_tuple,
    )
    if compiled is None:
        return
    _, _, _, constancy_info, h_insts = compiled

    target_vars = list(target_vars_tuple)
    intro = f"intro {' '.join(target_vars)}"
    default_fill = target_vars[0]
    emitted = 0

    if target_lhs_norm in h_insts:
        for intermediate_norm, args in h_insts[target_lhs_norm].items():
            intermediate_tree = _tree_from_normalized_expr(intermediate_norm)
            if intermediate_tree is None:
                continue
            if intermediate_tree == target_rhs_tree:
                continue
            steps = find_constancy_steps(
                intermediate_tree, target_rhs_tree, constancy_info, default_fill
            )
            if not steps:
                continue
            symm = args.endswith("|symm")
            h_args = args.replace("|symm", "")
            h_step = f"(h {h_args}).symm" if symm else f"h {h_args}"
            have_lines, used = _constancy_have_lines(steps, constancy_info)
            intermediate = tree_to_str(intermediate_tree)
            calc_lines = [f"calc {target_lhs}", f"  _ = {intermediate} := {h_step}"]
            current_tree = intermediate_tree
            for index, (path, cargs, csymm, info_index) in enumerate(steps):
                name = used[info_index]
                inner = f"({name} {cargs})" if not csymm else f"({name} {cargs}).symm"
                step_proof = wrap_congr_arg(current_tree, path, inner)
                current_tree = apply_rewrite_at(
                    current_tree, path, get_subtree(target_rhs_tree, path)
                )
                current_text = tree_to_str(current_tree)
                if index < len(steps) - 1:
                    calc_lines.append(f"  _ = {current_text} := {step_proof}")
                else:
                    calc_lines.append(f"  _ = {target_rhs} := {step_proof}")
            yield f"{intro}\n" + "\n".join(have_lines) + "\n" + "\n".join(calc_lines)
            emitted += 1
            if emitted >= max_candidates:
                return

    if target_rhs_norm in h_insts:
        for intermediate_norm, _ in h_insts[target_rhs_norm].items():
            if intermediate_norm not in h_insts or target_rhs_norm not in h_insts[intermediate_norm]:
                continue
            intermediate_tree = _tree_from_normalized_expr(intermediate_norm)
            if intermediate_tree is None:
                continue
            if target_lhs_tree == intermediate_tree:
                continue
            steps = find_constancy_steps(
                target_lhs_tree, intermediate_tree, constancy_info, default_fill
            )
            if not steps:
                continue
            args = h_insts[intermediate_norm][target_rhs_norm]
            symm = args.endswith("|symm")
            h_args = args.replace("|symm", "")
            h_step = f"(h {h_args}).symm" if symm else f"h {h_args}"
            have_lines, used = _constancy_have_lines(steps, constancy_info)
            calc_lines = [f"calc {target_lhs}"]
            current_tree = target_lhs_tree
            for path, cargs, csymm, info_index in steps:
                name = used[info_index]
                inner = f"({name} {cargs})" if not csymm else f"({name} {cargs}).symm"
                step_proof = wrap_congr_arg(current_tree, path, inner)
                current_tree = apply_rewrite_at(
                    current_tree, path, get_subtree(intermediate_tree, path)
                )
                calc_lines.append(f"  _ = {tree_to_str(current_tree)} := {step_proof}")
            calc_lines.append(f"  _ = {target_rhs} := {h_step}")
            yield f"{intro}\n" + "\n".join(have_lines) + "\n" + "\n".join(calc_lines)
            emitted += 1
            if emitted >= max_candidates:
                return


def iter_hconst_sandwich_match_collapse_proof_bodies(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
    max_h_instantiations: int = 200_000,
) -> Iterator[str]:
    source_equation = normalize_op_to_diamond(source_equation)
    target = _parse_hconst_target(target_equation)
    if target is None:
        return
    (
        target_lhs,
        target_rhs,
        target_lhs_norm,
        target_rhs_norm,
        target_vars_tuple,
        target_lhs_tree,
        target_rhs_tree,
    ) = target

    source_parts = source_equation.split("=", 1)
    if len(source_parts) != 2:
        return
    source_lhs = source_parts[0].strip()
    source_rhs = source_parts[1].strip()
    source_vars = parse_variables(source_equation)
    if not source_vars:
        return
    constancy_info, _, _ = build_constancy_info(
        source_equation,
        source_vars,
        list(target_vars_tuple),
    )
    if not constancy_info:
        return
    source_lhs_tree = parse_op_tree(source_lhs)
    source_rhs_tree = parse_op_tree(source_rhs)
    source_var_set = set(source_vars)
    terms = _target_terms_for_deep_hinst(
        target_lhs_tree,
        target_rhs_tree,
        target_vars_tuple,
    )

    target_vars = list(target_vars_tuple)
    intro = f"intro {' '.join(target_vars)}"
    default_fill = target_vars[0]
    first_edges = list(
        _h_edges_from_target_expr(
            target_tree=target_lhs_tree,
            source_lhs_tree=source_lhs_tree,
            source_rhs_tree=source_rhs_tree,
            source_vars=source_vars,
            source_var_set=source_var_set,
            terms=terms,
            max_instantiations=max_h_instantiations,
        )
    )
    if not first_edges:
        return
    final_edges = list(
        _h_preimage_edges_to_target_expr(
            target_tree=target_rhs_tree,
            source_lhs_tree=source_lhs_tree,
            source_rhs_tree=source_rhs_tree,
            source_vars=source_vars,
            source_var_set=source_var_set,
            terms=terms,
            max_instantiations=max_h_instantiations,
        )
    )
    if not final_edges:
        return
    emitted = 0
    seen_bodies: set[str] = set()
    for intermediate1_tree, first_args in first_edges:
        for intermediate2_tree, final_args in final_edges:
            if intermediate2_tree == target_lhs_tree:
                continue
            steps = find_constancy_steps(
                intermediate1_tree,
                intermediate2_tree,
                constancy_info,
                default_fill,
                max_steps=3,
            )
            if not steps:
                continue
            have_lines, used = _constancy_have_lines(steps, constancy_info)
            calc_lines = [
                f"calc {target_lhs}",
                f"  _ = {tree_to_str(intermediate1_tree)} := {_h_proof_from_args(first_args)}",
            ]
            current_tree = intermediate1_tree
            for path, cargs, csymm, info_index in steps:
                name = used[info_index]
                inner = f"({name} {cargs})" if not csymm else f"({name} {cargs}).symm"
                step_proof = wrap_congr_arg(current_tree, path, inner)
                current_tree = apply_rewrite_at(
                    current_tree,
                    path,
                    get_subtree(intermediate2_tree, path),
                )
                calc_lines.append(
                    f"  _ = {tree_to_str(current_tree)} := {step_proof}"
                )
            calc_lines.append(f"  _ = {target_rhs} := {_h_proof_from_args(final_args)}")
            body = f"{intro}\n" + "\n".join(have_lines) + "\n" + "\n".join(calc_lines)
            if body in seen_bodies:
                continue
            seen_bodies.add(body)
            yield body
            emitted += 1
            if emitted >= max_candidates:
                return


def iter_hconst_default_sandwich_match_collapse_proof_bodies(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
    max_constancy_steps: int = 4,
) -> Iterator[str]:
    source_equation = normalize_op_to_diamond(source_equation)
    target = _parse_hconst_target(target_equation)
    if target is None:
        return
    (
        target_lhs,
        target_rhs,
        _target_lhs_norm,
        _target_rhs_norm,
        target_vars_tuple,
        target_lhs_tree,
        target_rhs_tree,
    ) = target

    source_parts = source_equation.split("=", 1)
    if len(source_parts) != 2:
        return
    source_lhs = source_parts[0].strip()
    source_rhs = source_parts[1].strip()
    source_vars = parse_variables(source_equation)
    if not source_vars or not target_vars_tuple:
        return
    constancy_info, _, _ = build_constancy_info(
        source_equation,
        source_vars,
        list(target_vars_tuple),
    )
    if not constancy_info:
        return

    source_lhs_tree = parse_op_tree(source_lhs)
    source_rhs_tree = parse_op_tree(source_rhs)
    source_var_set = set(source_vars)
    target_vars = list(target_vars_tuple)
    default_fill = target_vars[0]
    first_edges = list(
        _h_edges_from_target_expr_default_fill(
            target_tree=target_lhs_tree,
            source_lhs_tree=source_lhs_tree,
            source_rhs_tree=source_rhs_tree,
            source_vars=source_vars,
            source_var_set=source_var_set,
            default_fill=default_fill,
        )
    )
    final_edges = list(
        _h_preimage_edges_to_target_expr_default_fill(
            target_tree=target_rhs_tree,
            source_lhs_tree=source_lhs_tree,
            source_rhs_tree=source_rhs_tree,
            source_vars=source_vars,
            source_var_set=source_var_set,
            default_fill=default_fill,
        )
    )
    if not first_edges or not final_edges:
        return

    intro = f"intro {' '.join(target_vars)}"
    emitted = 0
    seen_bodies: set[str] = set()
    for intermediate1_tree, first_args in first_edges:
        for intermediate2_tree, final_args in final_edges:
            if intermediate2_tree == target_lhs_tree:
                continue
            steps = find_constancy_steps(
                intermediate1_tree,
                intermediate2_tree,
                constancy_info,
                default_fill,
                max_steps=max_constancy_steps,
            )
            if not steps:
                continue
            have_lines, used = _constancy_have_lines(steps, constancy_info)
            calc_lines = [
                f"calc {target_lhs}",
                f"  _ = {tree_to_str(intermediate1_tree)} := {_h_proof_from_args(first_args)}",
            ]
            current_tree = intermediate1_tree
            for path, cargs, csymm, info_index in steps:
                name = used[info_index]
                inner = f"({name} {cargs})" if not csymm else f"({name} {cargs}).symm"
                step_proof = wrap_congr_arg(current_tree, path, inner)
                current_tree = apply_rewrite_at(
                    current_tree,
                    path,
                    get_subtree(intermediate2_tree, path),
                )
                calc_lines.append(
                    f"  _ = {tree_to_str(current_tree)} := {step_proof}"
                )
            calc_lines.append(f"  _ = {target_rhs} := {_h_proof_from_args(final_args)}")
            body = f"{intro}\n" + "\n".join(have_lines) + "\n" + "\n".join(calc_lines)
            if body in seen_bodies:
                continue
            seen_bodies.add(body)
            yield body
            emitted += 1
            if emitted >= max_candidates:
                return


def _h_rewrite_args_between(
    subtree_a: Tree,
    subtree_b: Tree,
    *,
    source_lhs_tree: Tree,
    source_rhs_tree: Tree,
    source_vars: list[str],
    source_var_set: set[str],
    terms: tuple[str, ...],
    max_instantiations: int,
) -> str | None:
    lhs_subst = unify_tree(source_lhs_tree, subtree_a, source_var_set)
    if lhs_subst is not None:
        rhs_subst = unify_tree(
            source_rhs_tree,
            subtree_b,
            source_var_set,
            dict(lhs_subst),
        )
        if rhs_subst is not None:
            for subst in _fill_source_substs(
                rhs_subst,
                source_vars,
                terms,
                max_instantiations,
            ):
                return " ".join(subst[variable] for variable in source_vars)

    rhs_subst = unify_tree(source_rhs_tree, subtree_a, source_var_set)
    if rhs_subst is not None:
        lhs_subst = unify_tree(
            source_lhs_tree,
            subtree_b,
            source_var_set,
            dict(rhs_subst),
        )
        if lhs_subst is not None:
            for subst in _fill_source_substs(
                lhs_subst,
                source_vars,
                terms,
                max_instantiations,
            ):
                return " ".join(subst[variable] for variable in source_vars) + "|symm"
    return None


def find_h_rewrite_step(
    tree_a: Tree,
    tree_b: Tree,
    *,
    source_lhs_tree: Tree,
    source_rhs_tree: Tree,
    source_vars: list[str],
    source_var_set: set[str],
    terms: tuple[str, ...],
    max_instantiations: int,
    path_prefix: str = "",
) -> tuple[str, str] | None:
    if tree_a == tree_b:
        return None
    args = _h_rewrite_args_between(
        tree_a,
        tree_b,
        source_lhs_tree=source_lhs_tree,
        source_rhs_tree=source_rhs_tree,
        source_vars=source_vars,
        source_var_set=source_var_set,
        terms=terms,
        max_instantiations=max_instantiations,
    )
    if args is not None:
        return path_prefix, args
    if tree_a[0] == "op" and tree_b[0] == "op":
        if tree_a[1] != tree_b[1]:
            left = find_h_rewrite_step(
                tree_a[1],
                tree_b[1],
                source_lhs_tree=source_lhs_tree,
                source_rhs_tree=source_rhs_tree,
                source_vars=source_vars,
                source_var_set=source_var_set,
                terms=terms,
                max_instantiations=max_instantiations,
                path_prefix=path_prefix + "L",
            )
            if left is not None:
                return left
        if tree_a[2] != tree_b[2]:
            right = find_h_rewrite_step(
                tree_a[2],
                tree_b[2],
                source_lhs_tree=source_lhs_tree,
                source_rhs_tree=source_rhs_tree,
                source_vars=source_vars,
                source_var_set=source_var_set,
                terms=terms,
                max_instantiations=max_instantiations,
                path_prefix=path_prefix + "R",
            )
            if right is not None:
                return right
    return None


def find_h_rewrite_steps(
    start_tree: Tree,
    goal_tree: Tree,
    *,
    source_lhs_tree: Tree,
    source_rhs_tree: Tree,
    source_vars: list[str],
    source_var_set: set[str],
    terms: tuple[str, ...],
    max_instantiations: int,
    max_steps: int = 3,
) -> list[tuple[str, str]]:
    steps: list[tuple[str, str]] = []
    current = start_tree
    for _ in range(max_steps):
        if current == goal_tree:
            break
        step = find_h_rewrite_step(
            current,
            goal_tree,
            source_lhs_tree=source_lhs_tree,
            source_rhs_tree=source_rhs_tree,
            source_vars=source_vars,
            source_var_set=source_var_set,
            terms=terms,
            max_instantiations=max_instantiations,
        )
        if step is None:
            return []
        steps.append(step)
        current = apply_rewrite_at(current, step[0], get_subtree(goal_tree, step[0]))
    return steps if current == goal_tree else []


def iter_hstep_default_sandwich_match_collapse_proof_bodies(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
    max_h_steps: int = 3,
    max_step_instantiations: int = 5000,
) -> Iterator[str]:
    source_equation = normalize_op_to_diamond(source_equation)
    target = _parse_hconst_target(target_equation)
    if target is None:
        return
    (
        target_lhs,
        target_rhs,
        _target_lhs_norm,
        _target_rhs_norm,
        target_vars_tuple,
        target_lhs_tree,
        target_rhs_tree,
    ) = target

    source_parts = source_equation.split("=", 1)
    if len(source_parts) != 2:
        return
    source_lhs = source_parts[0].strip()
    source_rhs = source_parts[1].strip()
    source_vars = parse_variables(source_equation)
    if not source_vars or not target_vars_tuple:
        return

    source_lhs_tree = parse_op_tree(source_lhs)
    source_rhs_tree = parse_op_tree(source_rhs)
    source_var_set = set(source_vars)
    target_vars = list(target_vars_tuple)
    terms = tuple(target_vars)
    first_edges = list(
        _h_edges_from_target_expr_term_fill(
            target_tree=target_lhs_tree,
            source_lhs_tree=source_lhs_tree,
            source_rhs_tree=source_rhs_tree,
            source_vars=source_vars,
            source_var_set=source_var_set,
            terms=terms,
            max_instantiations=max_step_instantiations,
        )
    )
    final_edges = list(
        _h_preimage_edges_to_target_expr_term_fill(
            target_tree=target_rhs_tree,
            source_lhs_tree=source_lhs_tree,
            source_rhs_tree=source_rhs_tree,
            source_vars=source_vars,
            source_var_set=source_var_set,
            terms=terms,
            max_instantiations=max_step_instantiations,
        )
    )
    if not first_edges or not final_edges:
        return

    intro = f"intro {' '.join(target_vars)}"
    emitted = 0
    seen_bodies: set[str] = set()
    for intermediate1_tree, first_args in first_edges:
        for intermediate2_tree, final_args in final_edges:
            if intermediate2_tree == target_lhs_tree:
                continue
            steps = find_h_rewrite_steps(
                intermediate1_tree,
                intermediate2_tree,
                source_lhs_tree=source_lhs_tree,
                source_rhs_tree=source_rhs_tree,
                source_vars=source_vars,
                source_var_set=source_var_set,
                terms=terms,
                max_instantiations=max_step_instantiations,
                max_steps=max_h_steps,
            )
            if not steps:
                continue
            calc_lines = [
                f"calc {target_lhs}",
                f"  _ = {tree_to_str(intermediate1_tree)} := {_h_proof_from_args(first_args)}",
            ]
            current_tree = intermediate1_tree
            for path, args in steps:
                step_proof = wrap_congr_arg(current_tree, path, _h_proof_from_args(args))
                current_tree = apply_rewrite_at(
                    current_tree,
                    path,
                    get_subtree(intermediate2_tree, path),
                )
                calc_lines.append(
                    f"  _ = {tree_to_str(current_tree)} := {step_proof}"
                )
            calc_lines.append(f"  _ = {target_rhs} := {_h_proof_from_args(final_args)}")
            body = f"{intro}\n" + "\n".join(calc_lines)
            if body in seen_bodies:
                continue
            seen_bodies.add(body)
            yield body
            emitted += 1
            if emitted >= max_candidates:
                return


def matches_hconst_match_collapse(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
) -> bool:
    source_equation = normalize_op_to_diamond(source_equation)
    target = _parse_hconst_target(target_equation)
    if target is None:
        return False
    (
        _target_lhs,
        _target_rhs,
        target_lhs_norm,
        target_rhs_norm,
        target_vars_tuple,
        target_lhs_tree,
        target_rhs_tree,
    ) = target
    compiled = _compile_hconst_source_for_target_vars(
        source_equation,
        target_vars_tuple,
    )
    if compiled is None:
        return False
    _, _, _, constancy_info, h_insts = compiled
    default_fill = target_vars_tuple[0]

    if target_lhs_norm in h_insts:
        for intermediate_norm in h_insts[target_lhs_norm]:
            intermediate_tree = _tree_from_normalized_expr(intermediate_norm)
            if intermediate_tree is None or intermediate_tree == target_rhs_tree:
                continue
            if find_constancy_steps(
                intermediate_tree,
                target_rhs_tree,
                constancy_info,
                default_fill,
            ):
                return True

    if target_rhs_norm in h_insts:
        for intermediate_norm in h_insts[target_rhs_norm]:
            if (
                intermediate_norm not in h_insts
                or target_rhs_norm not in h_insts[intermediate_norm]
            ):
                continue
            intermediate_tree = _tree_from_normalized_expr(intermediate_norm)
            if intermediate_tree is None or target_lhs_tree == intermediate_tree:
                continue
            if find_constancy_steps(
                target_lhs_tree,
                intermediate_tree,
                constancy_info,
                default_fill,
            ):
                return True

    return False


def matches_hstep_default_sandwich_match_collapse(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
    max_h_steps: int = 3,
    max_step_instantiations: int = 5000,
) -> bool:
    for _ in iter_hstep_default_sandwich_match_collapse_proof_bodies(
        source_equation,
        target_equation,
        max_candidates=max_candidates,
        max_h_steps=max_h_steps,
        max_step_instantiations=max_step_instantiations,
    ):
        return True
    return False


def matches_hconst_default_sandwich_match_collapse(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
    max_constancy_steps: int = 4,
) -> bool:
    for _ in iter_hconst_default_sandwich_match_collapse_proof_bodies(
        source_equation,
        target_equation,
        max_candidates=max_candidates,
        max_constancy_steps=max_constancy_steps,
    ):
        return True
    return False


def matches_hconst_sandwich_match_collapse(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
    max_h_instantiations: int = 200_000,
) -> bool:
    for _ in iter_hconst_sandwich_match_collapse_proof_bodies(
        source_equation,
        target_equation,
        max_candidates=max_candidates,
        max_h_instantiations=max_h_instantiations,
    ):
        return True
    return False


def make_true_code(proof_body: str) -> str:
    lines = proof_body.strip().splitlines()
    non_empty = [line for line in lines if line.strip()]
    if non_empty:
        min_indent = min(len(line) - len(line.lstrip()) for line in non_empty)
        lines = [line[min_indent:] if len(line) > min_indent else line for line in lines]
    indented = "\n".join("  " + line if line.strip() else "" for line in lines)
    return "import JudgeProblem\n\n" "def submission : Goal := by\n" "  intro G _ h\n" f"{indented}\n"


def render_first_hconst_match_collapse_certificate(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
) -> str | None:
    for proof_body in iter_hconst_match_collapse_proof_bodies(
        source_equation,
        target_equation,
        max_candidates=max_candidates,
    ):
        return make_true_code(proof_body)
    return None


def render_first_hstep_default_sandwich_match_collapse_certificate(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
    max_h_steps: int = 3,
    max_step_instantiations: int = 5000,
) -> str | None:
    for proof_body in iter_hstep_default_sandwich_match_collapse_proof_bodies(
        source_equation,
        target_equation,
        max_candidates=max_candidates,
        max_h_steps=max_h_steps,
        max_step_instantiations=max_step_instantiations,
    ):
        return make_true_code(proof_body)
    return None


def render_first_hconst_default_sandwich_match_collapse_certificate(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
    max_constancy_steps: int = 4,
) -> str | None:
    for proof_body in iter_hconst_default_sandwich_match_collapse_proof_bodies(
        source_equation,
        target_equation,
        max_candidates=max_candidates,
        max_constancy_steps=max_constancy_steps,
    ):
        return make_true_code(proof_body)
    return None


def render_first_hconst_sandwich_match_collapse_certificate(
    source_equation: str,
    target_equation: str,
    *,
    max_candidates: int = 64,
    max_h_instantiations: int = 200_000,
) -> str | None:
    for proof_body in iter_hconst_sandwich_match_collapse_proof_bodies(
        source_equation,
        target_equation,
        max_candidates=max_candidates,
        max_h_instantiations=max_h_instantiations,
    ):
        return make_true_code(proof_body)
    return None
