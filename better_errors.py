import re
from brian2.equations.equations import Equations


def friendly_equation_error(eq_string):
    # go through each line and check for common mistakes
    # we do this BEFORE letting brian try to parse
    # because brian's errors are too generic to be useful
    lines = eq_string.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        error = check_common_mistakes(line)
        if error:
            return error

    # if no common mistakes found, let brian try
    # if brian fails, we still try to add a helpful hint
    try:
        Equations(eq_string)
        return "No errors found."
    except Exception as e:
        return f"Brian says: {e}\n\nHint: {smart_hint(eq_string, str(e))}"


def check_common_mistakes(line):
    # brian has three equation types (from reading equations.py):
    # DIFF_EQ:   dv/dt = expr : unit
    # STATIC_EQ: x = expr : unit  
    # PARAMETER: x : unit   <- valid without '=', easy to mistake for error
    
    # detect parameter declarations first so we dont flag them wrongly
    # a parameter looks like "tau : second" - no = sign, that's fine
    is_parameter = bool(re.match(r'^\w+\s*:', line))

    # if there's an = sign but no colon, unit declaration is missing
    if ':' not in line and '=' in line:
        return (
            f"Missing unit declaration in:\n  '{line}'\n"
            f"Every equation needs ': unit' at the end.\n"
            f"Example: dv/dt = (El - v) / tau : volt"
        )

    # count brackets - mismatch is a common mistake
    if line.count('(') != line.count(')'):
        return (
            f"Mismatched parentheses in:\n  '{line}'\n"
            f"You have {line.count('(')} opening and "
            f"{line.count(')')} closing brackets."
        )

    # if there's a colon but no = and it doesn't look like a parameter
    # something is probably wrong
    if '=' not in line and ':' in line and not is_parameter:
        return (
            f"Missing '=' in:\n  '{line}'\n"
            f"Equations need the form: variable = expression : unit"
        )

    # brian uses python syntax, ^ doesn't mean power here
    # ** is the correct operator
    if '^' in line:
        return (
            f"Invalid operator '^' in:\n  '{line}'\n"
            f"Brian uses Python syntax. Use '**' for exponentiation.\n"
            f"Example: v**2 instead of v^2"
        )

    return None  # no problems found


def smart_hint(eq_string, error_msg):
    # try to give a slightly better hint based on what brian complained about
    if "unexpected" in error_msg.lower():
        return "Check for typos or unsupported symbols in your equation."
    if "dimension" in error_msg.lower():
        return "Your units might be inconsistent. Check both sides of the equation."
    return "Double-check your equation syntax against the Brian2 documentation."


if __name__ == "__main__":
    test_cases = [
        ("Missing unit",         "dv/dt = (El - v) / tau"),
        ("Mismatched parens",    "dv/dt = (El - v / tau : volt"),
        ("Wrong power operator", "dv/dt = v^2 / tau : volt"),
        ("Missing equals",       "dv/dt  tau : volt"),
        ("Valid parameter",      "tau : second"),
        ("Valid equation",       "dv/dt = (El - v) / tau : volt"),
    ]

    for description, eq in test_cases:
        print(f"\n{'='*50}")
        print(f"Test: {description}")
        print(f"Input: '{eq}'")
        print(f"Result: {friendly_equation_error(eq)}")