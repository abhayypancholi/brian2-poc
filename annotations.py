import re
from brian2.equations.equations import Equations


def parse_with_annotations(eq_string):
    # split the whole string into individual lines first
    # brian processes one equation per line so this makes sense
    lines = eq_string.strip().split('\n')
    
    annotations = {}  # will store variable_name -> comment
    clean_lines = []  # equations without comments, to pass to brian

    for line in lines:
        line = line.strip()
        
        # skip blank lines
        if not line:
            continue

        # this regex splits a line into two parts:
        # group 1 = everything before the #
        # group 2 = everything after the # (the comment)
        # the ? makes the comment part optional
        match = re.match(r'^([^#]+?)(?:\s*#\s*(.*))?$', line)
        
        if match:
            equation_part = match.group(1).strip()
            comment = match.group(2).strip() if match.group(2) else None
            
            # always keep the clean equation for brian
            clean_lines.append(equation_part)

            if comment:
                # figure out which variable this comment belongs to
                # brian has two equation types that have variables:
                # differential: dv/dt = ...  -> variable is v
                # static/parameter: I_total = ... -> variable is I_total
                diff_match = re.match(r'^d(\w+)/dt', line.strip())
                if diff_match:
                    # it's a differential equation like dv/dt
                    var = diff_match.group(1)
                else:
                    # static equation or parameter, variable is before =
                    var = line.split('=')[0].strip()

                annotations[var] = comment

    # join clean lines and let brian parse normally
    clean_eq_string = '\n'.join(clean_lines)
    equations = Equations(clean_eq_string)
    
    return equations, annotations


if __name__ == "__main__":
    eqs_string = """
    dv/dt = (El - v) / tau : volt  # membrane potential, resting at -70mV
    dg/dt = -g / tau_g : siemens   # synaptic conductance
    """

    equations, annotations = parse_with_annotations(eqs_string)
    print("=== Parsed Equations ===")
    print(equations)
    print("\n=== Extracted Annotations ===")
    for var, note in annotations.items():
        print(f"  {var}: '{note}'")