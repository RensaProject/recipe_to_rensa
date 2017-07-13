'''
Simple recipe extraction into a Rensa brain (Simprel recipe format).
'''
import spacy
import nodebox_linguistics_extended as nle
from ingredient_parser.en import parse
from instrparse import write_recipe_instruction_assertions
from ingredparse import interpret_parsed_ingredient
from ingredparse import resolve_multiple_units
from recipeworddata import instr_verbs
from Recipe import *
import io

'''
Attempts to determine whether a statement is simply listing ingredients or is an instruction.  Currently, this is an extremely simplified function that only checks if the statement ends in a period.  We assume that only recipe ingredients and instructions are included in the input text file.
'''
def is_ingredient_statement(line):
    return not line.endswith(".")

'''
Manages the translation from text to a recipe ingredient assertion.
'''
def get_recipe_ingredient_assertion(line):
    if is_ingredient_statement(line):
        parsed = resolve_multiple_units(line)
        return write_recipe_ingred_assertion(line, parsed)
    return None

'''
Manages the translation from text to a recipe instruction assertion.
'''
def get_recipe_instruction_assertion(line, ingredients):
    assertions = []
    if not is_ingredient_statement(line):
        lines = line.split(".")
        for l in lines:
            new_as = write_recipe_instruction_assertions(l, ingredients)
            if new_as:
                assertions.extend(new_as)
                new_as=[]
        return assertions
    return None

'''
Returns a Rensa assertion representing the parsed concepts for a single recipe statement about a list ingredient.
'''
def write_recipe_ingred_assertion(line, parsed):
    if line != "":
        try:
            interpet_parsed = interpret_parsed_ingredient(parsed)
            left, quantity, comment, pre_assertions = interpet_parsed[0], interpet_parsed[1], interpet_parsed[2], interpet_parsed[3]

            return {
                "l":[left],
                "relation":"instance_of",
                "r":["ingredient"],
                "quantity":quantity,
                "comment": comment,
                "text": line
            }, pre_assertions
        except:
            return None
    return None

'''
Reads in an input file, and parses its content into Rensa assertions.  These assertions are saved in the assertions folder.

If the user responds "Y", all previous assertions will be deleted.  Otherwise, they will be kept.
'''
def extract_recipe(filename):
    assertions, ingredients = [],[]
    with io.open(filename, 'r', encoding="utf-8") as myfile:    
        s=myfile.read()
    for line in s.split("\n"):
        line = u""+line+""
        ingred_data = get_recipe_ingredient_assertion(line)

        if ingred_data is not None:
            # Add pre-instructions (instructions included as part of the ingredient list).
            assertions.extend(ingred_data[1])
            # Add ingredient list item assertion.
            assertion = ingred_data[0]
            ingredients.append(assertion["l"][0])
            assertions.append(assertion)
    sp=1
    for line in s.split("\n"):
        assertion = get_recipe_instruction_assertion(line, ingredients)
        if assertion is not None:
            for a in assertion:
                a['storypoints']=[{"at":sp}]
                sp+=1
            assertions.extend(assertion)

    ''' Make a recipe with these assertions. '''
    # Make a brain containing the recipe assertions.
    recipe_brain = make_brain(assertions)

    # Make an instance of a recipe with this brain.
    my_recipe = Recipe({"brain":recipe_brain})

    return my_recipe
