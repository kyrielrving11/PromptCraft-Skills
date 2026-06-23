# Prompt Structure Checklist

After building an enhanced prompt, verify it covers these elements before presenting
to the user. Sections required depend on the cognitive-load level from Step 1 —
not all elements apply to every task. Skip any that have no substance.

## By Cognitive Load

### Low Load (≤3 sections)
- [ ] **Task**: Stated unambiguously in one sentence.
- [ ] **Input**: Target code, file, or scenario specified.
- [ ] **Hard Constraints**: Present only if there are real, non-negotiable rules. Omit the entire section otherwise.

Verify: No role, no output format, no examples, no generation requirements.
These are noise for simple one-line changes.

### Medium Load (5-7 sections)
- [ ] **Role**: Clear, specific, with domain and tech stack.
- [ ] **Task**: One sentence.
- [ ] **Input**: Target data/code/scenario.
- [ ] **Output Format**: Numbered deliverables. "具体实现要求" folded in per-item — no separate verbose section.
- [ ] **Format Reference Examples**: Only if cases were generated (Step 2.5) or user-supplied. Skip if neither — do NOT write `[待用户填写]`.
- [ ] **Hard Constraints**: Non-negotiable rules. Omit if empty.
- [ ] **Generation Requirements**: Acceptance criteria proportional to task size.

### High Load (8 sections)
- [ ] **Role**
- [ ] **Task**
- [ ] **Input**
- [ ] **Output Format**
- [ ] **Format Reference Examples**
- [ ] **具体实现要求 (Detailed Implementation Requirements)**
- [ ] **硬约束 (Hard Constraints)**
- [ ] **生成要求 (Generation Requirements)**

## Technique Alignment

After construction, verify the prompt matches the output template of the selected technique. Each reference file includes a **Prompt Output Template** section that defines the exact output skeleton.

- [ ] **Zero-Shot**: Prompt is light (≤3 sections). No role, no examples, no reasoning frames. Task + Input + Hard Constraints (only if real).
- [ ] **Few-Shot**: Medium-load structure. Section 5 is "格式参考示例（Few-Shot）" with 2-3 input→output pairs + mapping rule summary box. Examples are task-domain real data, NOT meta-examples of prompt design.
- [ ] **Zero-Shot-CoT**: Section 5 is a reasoning skeleton (format hint only, no concrete reasoning content). "先推理 → 再答案" structure.
- [ ] **Few-Shot-CoT**: Section 5 is "推理模式参考" with 2 input→reasoning→output triples + reasoning pattern migration box.
- [ ] **Step-Back**: Section 5 contains 2-3 abstraction framework ASCII boxes. Section 6 starts with transition sentence "基于上述抽象框架，实现以下所有功能".
- [ ] **Least-to-Most**: Section 5 contains 4-6 ordered subproblems (目标→要求→示例). Last subproblem is "综合实现完整模块". Section 6 expands by output format items, not by subproblems.
- [ ] **Tree-of-Thought**: Section 5 includes search strategy declaration, evaluation criteria table, and thought-tree state table format. Branch count ≤4, depth ≤3.

## Anti-Patterns to Avoid

- [ ] No generic advice without concrete application ("be careful" without saying HOW).
- [ ] No hidden reasoning chains that the end-user model can't see.
- [ ] No mixed unrelated tasks in a single prompt.
- [ ] **No placeholder sections.** Never write `[待用户填写]` or equivalent. If a section has no substance, skip it.
- [ ] No implicit assumptions about the user's environment or stack.
- [ ] No role assignment for Low-load tasks — "You are a senior software engineer" adds zero signal for "rename this variable".
- [ ] No forced output-format or generation-requirements sections for Low-load tasks.
