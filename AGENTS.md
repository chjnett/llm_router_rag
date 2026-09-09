# Project Interaction and Visual Rules

## Response style

- Apply the installed `i-have-adhd` skill until the user says `stop adhd mode` or `normal mode`.
- Lead with the result or the next action. Suppress preambles, tangents, duplicate recap, and closing pleasantries.
- Number multi-step actions, keep lists to five items or fewer, and give concrete time estimates.
- Restate the current step briefly on progress turns. Ask the user only when a decision cannot be made safely from repository evidence.

## Figures

- Use the installed `diagram-design` skill for new research figures, charts, flows, and explanatory diagrams.
- Default to minimal-light, static, self-contained HTML/SVG. Use a pure white background, black primary text and strokes, neutral gray secondary text, and no purple.
- Author explanatory labels in Korean. Preserve model IDs, metrics, commands, and technical identifiers exactly.
- Prefer deletion and a table over a diagram when the visual would not materially improve understanding.

## Architecture diagrams

- Use the installed `archify` skill for architecture, workflow, sequence, data-flow, and lifecycle explanations.
- Author all explanatory content in Korean. Use light/classic presentation with a white background, black text, neutral-gray borders, and no purple.
- Keep static output unless motion is explicitly requested. Use `meta.quality_profile: "showcase"`, validate all nine checks, deliver atomically, then run `visual-check` before handoff.
- Because Archify Viewer UI does not support Korean locale, omit `meta.locale`, keep authored content Korean, and disclose that fixed viewer controls fall back to English.

## Scope

These rules apply to new work. Do not restyle or regenerate existing figures and architecture artifacts unless the user asks.
