import os
from rensabrain.Brain import *
from main import extract_recipe
from Recipe import *

def main():
    current_dir = os.path.dirname(__file__) 

    ''' Extract a recipe structure from a text file. '''
    fn = 'input/lavender-pork-steaks.txt'
    my_recipe = extract_recipe(os.path.join(current_dir, fn))

    ''' Realize the recipe. '''
    print "\nHere is the recipe I extracted: "
    # Realize the recipe instance.
    print my_recipe.realize()

    ''' Save recipe data to file. '''
    # Save the recipe instance's brain as a JSON file in the assertions folder.
    my_recipe.save(os.path.join(current_dir, "assertions/"))

    # You can also save a recipe brain directly with this command:
    # recipe_brain.save_brain(os.path.join(current_dir, "assertions/"))

    ''' Delete old recipe data. '''
    # Delete old assertion files so that only the latest file is in the assertions folder.  Type "N" if you want to retain saved assertion files.  Comment out this line if you would like to always keep assertion files.
    delete_old_assertions(os.path.join(current_dir, "assertions/"))

    ''' Make a recipe brain from a set of assertions. '''
    assertions = [{
        "l":["sage"],
        "relation":"instance_of",
        "r":["ingredient"]
    }]
    recipe_brain_1 = make_brain(assertions)

    ''' Load recipe data from file. '''
    recipe_brain_2 = load_brain([os.path.join(current_dir, 'input/example-recipe-load.json')])

    ''' Make an instance of a recipe from a brain. '''
    # You can optionally title your recipe with the name attribute.
    my_recipe1 = Recipe({"brain":recipe_brain_1})
    my_recipe2 = Recipe({"name":"Grape Salad","brain":recipe_brain_2})

    ''' Substitute ingredients. '''
    # Note: this will only work in simple recipes that do not use specific amounts of an ingredient during instruction steps.
    my_recipe2.substitute(
        ("pecans","3 tablespoons"),
        ("raisins","1/4 cup")
    )

    ''' Change the name of a recipe. '''
    my_recipe2.name = "Better Grape Salad"
    
    # Let's check out the modified recipe.
    print my_recipe2.realize()

if __name__ == '__main__':
    main()
