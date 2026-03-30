from annotations import parse_with_annotations
from better_errors import friendly_equation_error

print("=" * 60)
print("BRIAN2 IMPROVED PARSER - PROOF OF CONCEPT")
print("by Abhay Pancholi | GSoC 2026 Application")
print("=" * 60)

# --- DEMO 1 ---
# showing that brian currently loses comments entirely
# and that we can preserve them as annotations

print("\n📌 DEMO 1: Comment Preservation as Annotations")
print("-" * 60)

eqs_string = """
dv/dt = (El - v) / tau : volt       # membrane potential
dg/dt = -g / tau_g : siemens        # synaptic conductance
I_total = I_ext + g * (E_rev - v) : amp  # total current
"""

equations, annotations = parse_with_annotations(eqs_string)

print("\nCurrent Brian2 output (comments lost):")
print(equations)

print("\nWith improved parser (comments preserved):")
for var, note in annotations.items():
    print(f"  Variable '{var}' → annotation: '{note}'")

# --- DEMO 2 ---
# showing that we can give better error messages
# than brian's generic "parsing failed at position x"

print("\n\n📌 DEMO 2: Helpful Error Messages")
print("-" * 60)

broken_equations = [
    ("Missing unit",         "dv/dt = (El - v) / tau"),
    ("Mismatched parens",    "dv/dt = (El - v / tau : volt"),
    ("Wrong power operator", "dv/dt = v^2 / tau : volt"),
    ("Missing equals sign",  "dv/dt  tau : volt"),
]

for description, eq in broken_equations:
    print(f"\n✗ {description}:")
    print(f"  Input   : {eq}")
    print(f"  Message : {friendly_equation_error(eq)}")

# --- DEMO 3 ---
# valid equations should pass through without any errors
# including parameter declarations which have no = sign by design

print("\n\n📌 DEMO 3: Valid Equations Pass Cleanly")
print("-" * 60)

valid_cases = [
    ("Differential equation", "dv/dt = (El - v) / tau : volt"),
    ("Parameter declaration",  "tau : second"),
]

for description, eq in valid_cases:
    print(f"\n✓ {description}:")
    print(f"  Input  : {eq}")
    print(f"  Result : {friendly_equation_error(eq)}")

print("\n" + "=" * 60)
print("See README.md for full explanation and next steps.")
print("=" * 60)