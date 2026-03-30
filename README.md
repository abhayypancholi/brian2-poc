# Brian2 Parser — Proof of Concept
### GSoC 2026 Application | Project 3: Improved Parser for Brian Model Descriptions
**Applicant:** Abhay Pancholi | B.Tech AI & Data Engineering | MNIT Jaipur

---

## What This Project Is About

Brian2 is an open-source simulator for biological spiking neural networks.
Researchers describe neuron models using a domain-specific language like this:
```python
eqs = '''
dv/dt = (El - v) / tau : volt   # membrane potential
dg/dt = -g / tau_g : siemens    # synaptic conductance
'''
```

After reading the Brian2 source code directly, I found two concrete problems.

---

## Requirements

- Python 3.8+
- Brian2 (`pip install brian2`)

## Setup
```bash
cd brian2-poc-master
pip install brian2
python demo.py
```

---

## Problem 1 — Comments Are Captured But Never Stored

This is more nuanced than it first appears. There are two separate
comment-handling situations in Brian2:

**In `brian2/equations/equations.py` (line 83 and 125):**
Comments in equation definitions are thrown away entirely using
pyparsing's `.ignore()`:
```python
# Line 83
(CharsNotIn(":#\n") + Suppress(Optional(LineEnd()))).ignore("#" + restOfLine)

# Line 125
EQUATION = (PARAMETER_EQ | STATIC_EQ | DIFF_EQ).ignore("#" + restOfLine)
```

**In `brian2/parsing/statements.py` (lines 21-22):**
Comments in reset/threshold code statements ARE captured by the grammar:
```python
COMMENT = Optional(CharsNotIn("#")).set_results_name("comment")
STATEMENT = VARIABLE + OP + EXPR + Optional(Suppress("#") + COMMENT)
```

`parse_statement()` even returns the comment as its fourth value.
The docstring shows the intended behaviour:
```python
>>> parse_statement('v = -65*mV  # reset the membrane potential')
('v', '=', '-65*mV', 'reset the membrane potential')
```

However, reading every caller of `parse_statement()` reveals the
comment is captured and then immediately discarded every single time:
```python
# brian2/codegen/translation.py line 237
var, op, expr, comment = parse_statement(line.code)
# 'comment' is never used again after this line

# brian2/equations/unitcheck.py line 89  
varname, op, expr, comment = parse_statement(line)
# 'comment' is never used again after this line
```

The same pattern appears in `codegen/generators/GSL_generator.py`.

So the full picture is: comments are either silently ignored at the
grammar level (`equations.py`) or captured but thrown away at the
caller level (`statements.py`). Neither path stores annotations
for researcher use. The GSoC work is to complete what was started.

---

## Problem 2 — Error Messages Are Generic

In `brian2/equations/equations.py` lines 388-394, ALL equation
parsing failures produce the same unhelpful output:
```python
except ParseException as p_exc:
    raise EquationError(
        "Parsing failed: \n"
        + str(p_exc.line) + "\n"
        + " " * (p_exc.column - 1) + "^\n"
        + str(p_exc)
    ) from p_exc
```
If we run this
Equations("dv//dt = v / tau : volt")

This is what a researcher sees:
```
brian2.equations.equations.EquationError: Parsing failed: 
dv//dt = v / tau : volt
^
Expected end of text, found 'dv'  (at char 0), (line:1, col:1)
```

for Equations("dv/dt = v^2 / tau : volt")
The researcher sees:
'''
Traceback (most recent call last):
  File "c:\CODE\brian2\check.py", line 4, in <module>
    Equations("dv/dt = v^2 / tau : volt")
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "c:\CODE\brian2\brian2\equations\equations.py", line 619, in __init__
    self._equations = parse_string_equations(eqns)
                      ~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "c:\CODE\brian2\brian2\utils\caching.py", line 107, in cached_func
    func._cache[cache_key] = func(*args, **kwds)
                             ~~~~^^^^^^^^^^^^^^^
  File "c:\CODE\brian2\brian2\equations\equations.py", line 416, in parse_string_equations
    expression = Expression(p.sub(" ", expression))
  File "c:\CODE\brian2\brian2\equations\codestrings.py", line 108, in __init__
    str_to_sympy(code)
    ~~~~~~~~~~~~^^^^^^
  File "c:\CODE\brian2\brian2\parsing\sympytools.py", line 77, in str_to_sympy
    return _str_to_sympy(expr)
  File "c:\CODE\brian2\brian2\utils\caching.py", line 107, in cached_func
    func._cache[cache_key] = func(*args, **kwds)
                             ~~~~^^^^^^^^^^^^^^^
  File "c:\CODE\brian2\brian2\parsing\sympytools.py", line 83, in _str_to_sympy
    s_expr = SympyNodeRenderer().render_expr(expr)
  File "c:\CODE\brian2\brian2\parsing\rendering.py", line 59, in render_expr
    return self.render_node(node.body)
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "c:\CODE\brian2\brian2\parsing\rendering.py", line 65, in render_node
    return getattr(self, methname)(node)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "c:\CODE\brian2\brian2\parsing\rendering.py", line 290, in render_BinOp
    op = self.expression_ops[op_name]
         ~~~~~~~~~~~~~~~~~~~^^^^^^^^^
KeyError: 'BitXor'
'''

The researcher is left completely blank, was not told what went wrong exactly. The same pattern exists in
`brian2/parsing/statements.py` lines 52-57.

---

## This PoC Demonstrates Both Fixes

### Fix 1 — Comment Preservation as Annotations

Extract and store comments before passing equations to pyparsing,
instead of letting `.ignore()` discard them.

**Current Brian2:**
```
dg/dt = -g / tau_g : S
dv/dt = (El - v) / tau : V
```
Comments completely lost.

**With improved parser:**
```
=== Parsed Equations ===
dg/dt = -g / tau_g : S
dv/dt = (El - v) / tau : V

=== Extracted Annotations ===
  Variable 'v' → annotation: 'membrane potential'
  Variable 'g' → annotation: 'synaptic conductance'
  Variable 'I_total' → annotation: 'total current'
```

### Fix 2 — Helpful Error Messages

Intercept common mistakes before pyparsing sees them and return
actionable messages.

**Current Brian2:**
```
EquationError: Parsing failed:
dv/dt = (El - v) / tau
                      ^
Expected ':'

 File "c:\CODE\brian2\check.py", line 4, in <module>
    Equations("dv/dt = v^2 / tau : volt")
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "c:\CODE\brian2\brian2\equations\equations.py", line 619, in __init__
    self._equations = parse_string_equations(eqns)
                      ~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "c:\CODE\brian2\brian2\utils\caching.py", line 107, in cached_func
    func._cache[cache_key] = func(*args, **kwds)
                             ~~~~^^^^^^^^^^^^^^^
  File "c:\CODE\brian2\brian2\equations\equations.py", line 416, in parse_string_equations
    expression = Expression(p.sub(" ", expression))
  File "c:\CODE\brian2\brian2\equations\codestrings.py", line 108, in __init__
    str_to_sympy(code)
    ~~~~~~~~~~~~^^^^^^
  File "c:\CODE\brian2\brian2\parsing\sympytools.py", line 77, in str_to_sympy
    return _str_to_sympy(expr)
  File "c:\CODE\brian2\brian2\utils\caching.py", line 107, in cached_func
    func._cache[cache_key] = func(*args, **kwds)
                             ~~~~^^^^^^^^^^^^^^^
  File "c:\CODE\brian2\brian2\parsing\sympytools.py", line 83, in _str_to_sympy
    s_expr = SympyNodeRenderer().render_expr(expr)
  File "c:\CODE\brian2\brian2\parsing\rendering.py", line 59, in render_expr
    return self.render_node(node.body)
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "c:\CODE\brian2\brian2\parsing\rendering.py", line 65, in render_node
    return getattr(self, methname)(node)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "c:\CODE\brian2\brian2\parsing\rendering.py", line 290, in render_BinOp
    op = self.expression_ops[op_name]
         ~~~~~~~~~~~~~~~~~~~^^^^^^^^^
KeyError: 'BitXor'
```

**Improved:**
```
✗ Missing unit:
  Input   : dv/dt = (El - v) / tau
  Message : Missing unit declaration in:
  'dv/dt = (El - v) / tau'
Every equation needs ': unit' at the end.
Example: dv/dt = (El - v) / tau : volt

✗ Wrong power operator:
  Input   : dv/dt = v^2 / tau : volt
  Message : Invalid operator '^' in:
  'dv/dt = v^2 / tau : volt'
Brian uses Python syntax. Use '**' for exponentiation.
Example: v**2 instead of v^2
```

Other mistakes handled:
- Mismatched parentheses — counts opening vs closing brackets
- Missing `=` sign — detects malformed equation structure

---

## Files

| File | Purpose |
|---|---|
| `annotations.py` | Extracts comments before pyparsing strips them |
| `better_errors.py` | Intercepts common mistakes with clear messages |
| `demo.py` | Run this — shows both improvements side by side |

---

## Proposed Full GSoC Implementation

**For comment preservation:**
- In `equations.py`: replace `.ignore("#" + restOfLine)` at lines
  83 and 125 with a capture group using `.set_results_name("comment")`
- In `statements.py`: pass the already-captured `comment` value
  downstream instead of discarding it at each call site
- Store annotations as a dict on the `Equations` object
- Expose via `equations.annotations['v']` style API

**For error messages:**
- Expand the `except ParseException` block at line 388 in `equations.py`
- Expand the `except ParseException` block at line 52 in `statements.py`
- Use `p_exc.column` and `p_exc.line` that pyparsing already provides
  to generate context-aware hints
- Return specific messages based on which equation type was being
  parsed — DIFF_EQ, STATIC_EQ, or PARAMETER_EQ

**Files to change:**
- `brian2/equations/equations.py` — primary
- `brian2/parsing/statements.py` — fix callers to use comment
- `brian2/codegen/translation.py` — use comment instead of discarding
- `brian2/equations/unitcheck.py` — use comment instead of discarding

---

## About Me

B.Tech student in AI and Data Engineering at MNIT Jaipur,
entering 2nd year. I studied parsing theory independently and
will be taking a formal compiler design course in 2nd year.

I built this PoC after reading the Brian2 source directly.
The key finding — that `parse_statement()` already captures
comments but every single caller discards them — came from
tracing the function through `translation.py`, `unitcheck.py`,
and `GSL_generator.py`, not from documentation.