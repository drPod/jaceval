You are grading one candidate Jac-language solution to a programming task. You are NOT grading whether the code compiles or passes tests — a separate system does that. You are grading IDIOMATICITY: how well the candidate uses Jac-native constructs versus transliterating Python.

# Task rubric
{task_rubric}

# Reference idiomatic solution
```jac
{reference_solution}
```

# Candidate code
```jac
{candidate_code}
```

# Instructions

First, list which idiomatic Jac constructs appear in the candidate, citing line numbers. Be specific: "line 5 uses a `walker` archetype", not "uses walkers".

Second, for each level descriptor in the task rubric, write one sentence on whether the candidate meets it.

Third, if the candidate reads like Python-with-Jac-syntax — e.g., using `dict`-of-lists for what should be typed edges, using recursion instead of a walker with `visit`, omitting type annotations on `has` / params / returns, storing relationship data on nodes instead of typed edges, manual BFS over `[-->]` instead of a walker — this is a SERIOUS idiomaticity failure. Score 1 or 2 regardless of whether tests pass. **Jac is not Python; this is the single most important thing to catch.**

Finally, emit STRICTLY VALID JSON on its own line:
{{"constructs_present": [<strings>], "per_criterion": {{<rubric_item>: <1-5 int>}}, "feedback": "<1-3 sentences>", "score": <1-5 int>}}

Then on a new line emit: [RESULT] X   where X is your final score 1-5.
