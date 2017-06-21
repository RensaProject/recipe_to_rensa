'''
Simple ingredient extraction into a Rensa brain (Simprel format).
'''

from ingredient_parser.en import parse
from rensabrain.Brain import *

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def write_recipe_assertion(line, parsed):
    if line != "":
        try:
            if "," in parsed["name"]:
                left = parsed["name"].split(", ")[0].lower()
            else:
                left = parsed["name"].lower()
            meas = parsed["measure"]
            num_idx = len(meas)-1
            for c in reversed(meas):
                if is_number(c):
                    break;
                num_idx-=1;

            right_unit = parsed["measure"][num_idx+2:]
            right_num = parsed["measure"][:num_idx+1]
            comment = parsed["name"].split(", ")[1:]

            return {
                "l":[left],
                "relation":"instance_of",
                "r":["ingredient"], 
                "r_unit":[right_unit],
                "r_num":[right_num],
                "comment": comment,
                "text": line
            }
        except:
            return None
    return None

def main():
    assertions = []
    with open('input/recipe.txt', 'r') as myfile:
        s=myfile.read()
    for line in s.split("\n"):
        assertion = write_recipe_assertion(line, parse(line))
        if assertion is not None:
            assertions.append(assertion)
    recipe = make_brain(assertions)
    recipe.save_brain("assertions/")
    delete_old_assertions("assertions/")

if __name__ == '__main__':
    main()
