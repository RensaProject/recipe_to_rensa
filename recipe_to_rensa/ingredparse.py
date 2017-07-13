from ingredient_parser.en import parse
import nodebox_linguistics_extended as nle
from recipeworddata import *
import re

'''
Sometimes, chefs like to include two units of measure when specifying an ingredient.  For example:

1 cup + 3 tablespoons flour

This function ensures that the number and measure are correctly parsed in this case.
'''
def resolve_multiple_units(line):
    if "+" in line:
        parts = line.split(" + ")
        first = parse(parts[0])
        second = parse(parts[1])

        parsed = {
            'name': second["name"],
            'measure': [first["measure"] + first["name"], second["measure"]]
        }
    else:
        parsed=parse(line)
        parsed["measure"] = [parsed["measure"]]
    return parsed

'''
The ingredient_parser.en library is useful, but doesn't give us a detailed parse.  This function attempts to separate a parsed text of an ingredient list text further into ingredient name, unit, amount, and additional comments.
'''
# TODO: ingredient_parser.en isn't fond of avocados.
def interpret_parsed_ingredient(parsed):
    comment = {
        "properties":[],
        "misc":[]
    }
    if "," in parsed["name"]:
        left = parsed["name"].split(", ")[0].lower()
    else:
        left = parsed["name"].lower()

    left = " " + left

    left = left.replace("finely-","")
    left = left.replace("finely ","")

    # Extract ingredient properties.
    if any(q in left for q in ingredient_properties):
        for q in ingredient_properties:
            if " "+q+" " in left:
                left = left.replace (" "+q+" "," ")
                comment["properties"].append(q)

    # Extract information in parentheses.
    paren_notes = re.findall('\(.*?\)',left)
    for pn in paren_notes:
        comment["misc"].append(pn)
    left = re.sub(r'\([^)]*\)', '', left)

    pre_instrs = []
    if any(x in left for x in ingred_list_instrs):
        for instr in ingred_list_instrs:
            idx = left.find(" "+instr+" ")
            if idx!=-1:
                # left_instr = left[:idx+len(" "+instr+" ")]
                left_instr = left[idx+1:idx+len(" "+instr+" ")-1]
                left = left[:idx] + " " + left[idx+len(" "+instr+" "):]
                pre_instrs.append((left_instr.strip(),left.strip()))
    pre_assertions = interpret_pre_instrs(pre_instrs)

    right_unit, right_num = [],[]
    for meas in parsed["measure"]:
        num_idx = len(meas)-1
        for c in reversed(meas.split(" ")):
            if is_number_or_fraction(c):
                break;
            num_idx-=1+len(c);
        right_unit.append(meas[num_idx+2:])
        right_num.append(meas[:num_idx+1])
    comment["misc"].append(parsed["name"].split(", ")[1:])

    for ru in right_unit:
        if ru in ["small","medium","large"]:
            comment["properties"].append(ru)
    right_unit = [x if x not in ["small","medium","large"] else "" for x in right_unit]

    # TODO: note that if "package + (some other measure)", this will break.
    if not any(ru for ru in right_unit) and "package" in left:
        if "packages " in left:
            right_unit[-1] = "packages"
            left = left.replace("packages ", " ")
        elif "package " in left:
            right_unit[-1] = "package"
            left = left.replace("package ", " ")
    left = left.strip()
    left = left.replace("  "," ")

    # TODO add quantity range option
    quantity = {"type": "exact","values": []}
    for i,rn in enumerate(right_num):
        quantity["values"].append({"value":rn, "unit":right_unit[i]})

    return [left, quantity, comment, pre_assertions]

'''
Turns pre-instructions (instructions included in the ingredient list) into recipe instruction assertions.
'''
def interpret_pre_instrs(pre_instrs):
    pre_assertions = []
    for pi in pre_instrs:
        assertion = {
            "l": ["chef"],
            "relation": "action",
            "r": [],
            "action_object": [pi[1]],
            "grammatical_mood": "imperative",
            "type": "recipe instruction",
            "storypoints":[{"at":0}]
        }
        action = nle.verb.infinitive(pi[0])
        # A few exceptions NLE doesn't have yet.
        if pi=="juiced":
            action = "juice"
        if pi=="deveined":
            action="devein"
        if action!="":
            assertion["r"].append(action)
            pre_assertions.append(assertion)
    return pre_assertions


'''
Attempts to decide if a term is a number or a fraction.
'''
def is_number_or_fraction(term):
    if nle.is_number(term):
        return True
    term = term.replace("-"," ")
    ts = term.split(" ")
    for t in ts:
        if nle.is_number(t) or is_fraction(t):
            continue
        else:
            return False
    return True

'''
Attempts to decide if a term is a fraction.
'''
def is_fraction(term):
    if term in ["quarters","half","eighth","eighths","fourth","fourths"]:
        return True
    values = term.split('/')
    return len(values) == 2 and all(i.isdigit() for i in values) and values[1]!=0
