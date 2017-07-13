# Recipe to Rensa

## Overview
With this code, you can:
 - Extract ingredients and instructions from a recipe written in English.
 - Save this data as JSON.  
 - Make ingredient substitutions (or other changes to the recipe).
 - Realize recipe data in natural English.

## Example Usage
Let’s say we have a recipe for cookies stored in a file called `my_input.txt.`  That file might look like:
```
1 cup peanut butter
1 cup sugar
1 large egg

Combine 1 cup of peanut butter, sugar, and egg in a large bowl.  Shape dough into 1-inch balls.
Place balls 1 inch apart on ungreased baking sheets, and flatten gently with tines of a fork.
Bake at 325°F for 15 minutes or until golden brown. Remove to wire racks to cool.
```

To extract the recipe content, we can run the following command:
```
my_recipe = extract_recipe('my_input.txt')
```
This will extract nuggets of recipe information into JSON assertions.  The fact that we need 1 cup peanut butter, for example, is represented by an assertion structure wherein *peanut butter instance_of ingredient* with an *exact quantity* of *value: 1* and *unit: cup*.

The first instruction is interpreted as an action which connects a left-hand concept (*l*) “chef” to a right-hand concept (*r*) “combine” by an “action” relation.  This action encoding primarily consists of the following key-value pairs:
```
{
    "grammatical_mood": "imperative", 
    "l": ["chef"], 
    "relation": "action", 
    "r": ["combine"], 
    "action_objects": ["peanut butter", "sugar", "egg"],     
    "location_in": ["bowl"],     
    "condition_given": [
      {
        "l": ["bowl"],
        "relation": "has_property", 
        "r": ["large"]
      }
    ], 
    "type": "recipe instruction"
  }

```
Assertions like these are stored within the “brain” of my_recipe.

To substitute an equal amount of nutella for peanut butter:
```
my_recipe.substitute(
        ("peanut butter","1 cup"),
        ("nutella","1 cup")
    )
```

We can now realize the modified recipe structure into natural language:
```
print my_recipe.realize()
```
The output will read:

```
MY RECIPE

Ingredients:
1 cup nutella
1 cup sugar
1 egg

Instructions:
1. Combine nutella, sugar, and egg (using 1 cup nutella) in large bowl.
2. Shape dough into 1-inch balls.
3. Place balls on ungreased baking sheets.
4. Flatten with tines.
5. Bake for 15 minutes at 325 degrees Fahrenheit.
6. Remove.
7. Cool.
```

When you're finished, you can save the recipe data:
```
my_recipe.save("your/path/here/")
```

For more detailed examples, check out demo.py once you've finished installing:
```
python recipe_to_rensa/demo.py
```

## Installation
Download or clone the repository:
```
git clone https://github.com/RensaProject/recipe_to_rensa.git
cd recipe_to_rensa
```

Optional, but recommended: use virtualenv (or equivalent) to isolate environment:
```
virtualenv venv
source venv/bin/activate
```

Finally, install dependencies with `pip` and download the relevant spacy model:

```
pip install -r requirements.txt
python -m spacy download en
```

## License
If you use this repository, please cite:

```
@phdthesis{harmon2017narrative,
  title={Narrative Encoding for Computational Reasoning and Adaptation},
  author={Harmon, Sarah M},
  year={2017},
  school={University of California, Santa Cruz}
}
```
