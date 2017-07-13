# -*- coding: utf-8 -*-
from recipeworddata import *
import spacy
nlp = spacy.load('en')
import nodebox_linguistics_extended as nle
from Recipe import *
import string
from ingredparse import is_number_or_fraction
from ingredparse import interpret_parsed_ingredient
from ingredparse import resolve_multiple_units

'''
Takes in a string representing a single action, and returns the attributes and values for a corresponding assertion.
'''
def get_recipe_instr_content(s):
    # Initialize variables.
    look_for_of = False
    action = ""
    action_objects = []
    locations = []
    condition_givens = []
    condition_withs = []
    current_conj_subj = ""
    time_for = []
    temps = []
    quantities = []

    # Convert the input string into a doc.
    doc = nlp(u''+s+'')

    # For each noun chunk in the doc, let's check the dependency relation.
    for np in doc.noun_chunks:
        # Pobjs indicate conditions, locations...
        if np.root.dep_=="pobj":
            nps = str(np.text).split(" and ")
            for i,the_np in enumerate(nps):
                if np.root.head.text=="of" and look_for_of:
                    if i==len(nps)-1:
                        look_for_of = check_if_of(the_np)
                    if i==len(nps)-1 and look_for_of:
                        of_measure = the_np
                        parsed = resolve_multiple_units(of_measure + " flour")
                        quantities.append((current_conj_subj,interpret_parsed_ingredient(parsed)[1]))
                    else:
                        if current_conj_subj=="action_object":
                            ao = remove_stopwords(the_np)
                            ao_tuple = separate_entity_and_quality(ao)
                            action_objects.append(ao_tuple[0])
                            if ao_tuple[1] and ao_tuple[0]:
                                condition_givens.append({
                                    "l":[ao_tuple[0]],
                                    "relation":"has_property",
                                    "r": ao_tuple[1]
                                })
                            if i==0:
                                quantities[-1][1]["ingredient"]= separate_entity_and_quality(ao)[0]
                        elif current_conj_subj=="condition_with action_object":
                            ao = remove_stopwords(the_np)
                            ao_tuple = separate_entity_and_quality(ao)
                            condition_withs.append({
                                    "preposition": "with",
                                    "action_object": [ao_tuple[0]]
                                })
                            if i==0:
                                quantities[-1][1]["ingredient"]= separate_entity_and_quality(ao)[0]
                                condition_withs[-1]["action_object_quantity"] = [quantities[-1][1]]
                                quantities = quantities[:-1]
                            if ao_tuple[1] and ao_tuple[0]:
                                condition_givens.append({
                                    "l":[ao_tuple[0]],
                                    "relation":"has_property",
                                    "r": ao_tuple[1]
                                })
                elif np.root.head.text=="with":
                    current_conj_subj="condition_with action_object"
                    look_for_of = check_if_of(the_np)
                    if look_for_of:
                        of_measure = the_np
                        parsed = resolve_multiple_units(of_measure + " flour")
                        quantities.append(("condition_with action_object",interpret_parsed_ingredient(parsed)[1]))
                    else:
                        with_tuple = separate_entity_and_quality(remove_stopwords(the_np))
                        if with_tuple[0] != "door":
                            condition_withs.append({
                                "preposition": "with",
                                "action_object": [with_tuple[0]]
                            })
                            # TODO: Might want to change these to be in the condition_with.
                            if with_tuple[1] and with_tuple[0]:
                                condition_givens.append({
                                    "l":[with_tuple[0]],
                                    "relation":"has_property",
                                    "r": with_tuple[1]
                                })
                elif np.root.head.text=="for":
                    if any(time in the_np.lower().split(" ") for time in time_units):
                        time_for.append(preprocess_time_statement(str(np.text)))
                        current_conj_subj = "time_for"
                    elif any(temp in the_np for temp in abstract_temps):
                        temps.append({
                            "type": "abstract",
                            "value": str(np.text).replace(" heat","")
                        })
                elif np.root.head.text=="to" or np.root.head.text=="at" or np.root.head.text=="over":
                    at_what = the_np.replace(" - ","-")
                    if "degrees" in at_what:
                        temps.append({
                            "type": "specific",
                            "value": at_what
                        })
                        if not any(x in at_what.lower() for x in ["fahrenheit","celsius"]):
                            unit = ""
                            try:
                                degree_idx = s.find(" degrees ")
                                if degree_idx != -1:
                                    unit = s[degree_idx+2+len("degrees"):].split(" ")[0].title()
                            except:
                                pass
                            temps[-1]["value"] += " " + unit
                        else:
                            temps[-1]["value"] = temps[-1]["value"].replace("celsius","Celsius").replace("fahrenheit","Fahrenheit")
                    elif any(temp in at_what for temp in abstract_temps):
                        temps.append({
                            "type": "abstract",
                            "value": at_what.replace(" heat","")
                        })
                    else:
                        prep_tuple = separate_entity_and_quality(remove_stopwords(at_what))
                        condition_withs.append({
                            "preposition": str(np.root.head.text),
                            "action_object": [prep_tuple[0]]
                        })
                        if prep_tuple[1] and prep_tuple[0]:
                            condition_givens.append({
                                "l":[prep_tuple[0]],
                                "relation":"has_property",
                                "r": prep_tuple[1]
                            })
                elif np.root.head.text=="into" and action in shape_verbs:
                    shape_what = the_np.replace(" - ","-")
                    prep_tuple = separate_entity_and_quality(remove_stopwords(shape_what))
                    condition_withs.append({
                        "preposition": "into",
                        "action_object": [prep_tuple[0]]
                    })
                    if prep_tuple[1] and prep_tuple[0]:
                        condition_givens.append({
                            "l":[prep_tuple[0]],
                            "relation":"has_property",
                            "r": prep_tuple[1]
                        })
                elif np.root.head.text in locationPrepositions and "heat" not in the_np:
                    location_type = np.root.head.text
                    location_where = remove_stopwords(the_np.replace("and",","))
                    location_where_tuple = separate_entity_and_quality(location_where)
                    entity = location_where_tuple[0]
                    locations.append((location_type, entity))
                    if location_where_tuple[1] and entity:
                        condition_givens.append({
                            "l":[entity],
                            "relation":"has_property",
                            "r": location_where_tuple[1]
                        })
                    current_conj_subj = "location_" + location_type
        # Dobjs indicate an action is taking place.
        elif (np.root.dep_=="dobj" or np.root.dep_=="nsubj") and (np.root.head.text in instr_verbs or np.root.head.text in instr_and_ingred_words):
            nps = str(np.text).split(" and ")
            for the_np in nps:
                if the_np.lower()!="you":
                    look_for_of = check_if_of(the_np)
                    if look_for_of:
                        action = str(np.root.head.text)
                        of_measure = the_np
                        parsed = resolve_multiple_units(of_measure + " flour")
                        quantities.append(("action_object",interpret_parsed_ingredient(parsed)[1]))
                        current_conj_subj = "action_object"
                    else:
                        if any(time in the_np.lower().split(" ") for time in time_units):
                            time_for.append(preprocess_time_statement(the_np))
                            current_conj_subj = "time_for"
                        else:
                            action = str(np.root.head.text)
                            action_objects.append(remove_stopwords(the_np))
                            current_conj_subj = "action_object"
                else:
                    action = str(np.root.head.text)

        elif np.root.dep_=="conj":
            conj_what = [ remove_stopwords(e) for e in str(np.text).split(" and ")]
            for what in conj_what:
                look_for_of = check_if_of(np.text)
                if look_for_of:
                    of_measure = np.text
                    parsed = resolve_multiple_units(of_measure + " flour")
                    quantities.append((current_conj_subj, interpret_parsed_ingredient(parsed)[1]))
                else:
                    conj_tuple = separate_entity_and_quality(what)
                    entity = conj_tuple[0]
                    if current_conj_subj=="action_object":
                        action_objects.append(entity)
                    elif current_conj_subj=="condition_with action_object":
                        condition_withs[-1]["action_object"].append(entity)
                    elif current_conj_subj=="time_for":
                        time_for.append(preprocess_time_statement(str(np.text)))
                    if conj_tuple[1] and entity:
                        condition_givens.append({
                            "l":[entity],
                            "relation":"has_property",
                            "r": conj_tuple[1]
                        })

    # Postprocess.
    if action=="set" and "aside" in s:
        action="reserve"
    if action=="grate" and "oil grate" in s:
        action = "oil"
        action_objects.append("grate")
    if action=="turn":
        if " off " in s:
            action = "turn off"
        if " on " in s:
            action = "turn on"
    if (action=="set" or "heat" in action_objects) and not temps:
        s = s.replace(" - ","-")
        if any(temp in s for temp in abstract_temps):
            temps.extend([{"type":"abstract","value":temp.replace(" heat","")} for temp in abstract_temps if temp in s])
    if any(time in s for time in time_units) and not time_for:
        time_for.extend(get_time_fors(s))

    return {"action": action, "action_object": action_objects, "locations": locations, "condition_givens": condition_givens, "condition_withs": condition_withs, "time_for": time_for, "temps": temps, "quantities":quantities}

# TODO: distinguish between time_for and store (for) up to duration
# TODO: "overnight" commonly used as well
def get_time_fors(s):
    matches = []
    times = []
    for tu in time_units:
        matches += nle.sentence.find(s,"* (*) " + tu)
    for m in matches:
        substr = ""
        time = ""
        for i in m:
            for t in i:
                substr = t + " "
                if is_number_or_fraction(t):
                    time += (t + " ")
                elif t in time_units:
                    time += t
                    time.replace("  "," ")
                    times.append(time)
                    time = ""
    return times

'''
Removes unnecessary words in an identified string about time.
'''
def preprocess_time_statement(s):
    return s.replace("about ","").replace("around ","").replace("approximately ","").replace(" - ","-")

'''
Takes in a dict of assertion attributes for a recipe instruction, and returns an assertion in the proper format.
'''
def make_recipe_instr_assertion(d):
    assertion = {
        "l": ["chef"],
        "relation": "action",
        "r": [],
        "grammatical_mood": "imperative",
        "type": "recipe instruction"
    }
    try:
        assertion_action = nle.verb.infinitive(d["action"])
    except:
        assertion_action = d["action"]
    if assertion_action=="":
        assertion_action = d["action"]
    assertion["r"].append(assertion_action)

    if d["action_object"]:
        assertion["action_object"] = d["action_object"]

    if d["locations"]:
        for loc in d["locations"]:
            loc_type = "location_" + loc[0]
            if hasattr(assertion, loc_type):
                assertion[loc_type].append(loc[1])
            else:
                assertion[loc_type] = [loc[1]]

    if d["condition_givens"]:
        assertion["condition_given"] = []
        for cond in d["condition_givens"]:
            assertion["condition_given"].append(cond)

    if d["condition_withs"]:
        for cond in d["condition_withs"]:
            prep = cond["preposition"]
            if "condition_"+prep in assertion:
                assertion["condition_"+prep].append(cond)
            else:
                assertion["condition_"+prep]=[cond]

    if d["time_for"]:
        assertion["time_for"] = []
        for time in d["time_for"]:
            assertion["time_for"].append(time)

    if d["temps"]:
        assertion["temperature"] = []
        for temp in d["temps"]:
            assertion["temperature"].append(temp)

    if d["quantities"]:
        for quantity_tuple in d["quantities"]:
            if len(quantity_tuple[0].split(" "))==1:
                # e.g. "action_object_quantity"
                if quantity_tuple[0]+"_quantity" in assertion:
                    assertion[quantity_tuple[0]+"_quantity"].append(quantity_tuple[1])
                else:
                    assertion[quantity_tuple[0]+"_quantity"] = [quantity_tuple[1]]

    return assertion if assertion["r"]!=[''] else {}

'''
Returns the verb phrases in a sentence.
Examples:
    "In a medium bowl, mix two cups of the cake flour with baking soda."
    >> ['in a medium bowl , mix two cups of the cake flour with baking soda']

    "Heat olive oil in a skillet over medium heat until the oil shimmers, and place the flank steak into the hot oil."
    >> ['heat olive oil in a skillet over medium heat until the oil shimmers , and', 'place the flank steak into the hot oil']
'''
def get_verb_substrings(s):
    ss = []
    cur_string = ""
    add_to_add = False
    to_add = ""
    is_verb = False
    doc = nlp(u''+s+'')
    firstVerb = True
    for i, word in enumerate(doc):
        wtext = str(word.text)
        if str(word.text).lower() in ["let","allow"]:
            add_to_add = True
        else:
            if maybe_cooking_verb(i,word,doc):
                is_verb = True
                if word.tag_=="VBG":
                    new_word = nle.verb.infinitive(wtext.lower())
                    if new_word != "":
                        wtext = new_word
                if not firstVerb:
                    if cur_string:
                        ss.append(cur_string.lower().strip())
                    cur_string = ""
                else:
                    firstVerb = False
                cur_string += " you"
            if add_to_add:
                if is_verb:
                    cur_string += " " + wtext + " " + to_add.strip()
                    add_to_add = False
                    is_verb = False
                else:
                    to_add += wtext + " "
            else:
                cur_string += " " + wtext
    if cur_string and cur_string.strip()!=".":
        ss.append(cur_string.lower().strip())
    return ss

'''
Attempts to determine if this is a verb for a cooking phrase (helper for get_verb_substrings()).
'''
def maybe_cooking_verb(i,word,doc):
    wtext = str(word.text).lower()
    ptext,ptag,ppos,ntext,npos = "","","","",""
    if i>0:
        ptext = str(doc[i-1].text).lower()
        ptag = doc[i-1].tag_
        ppos = doc[i-1].pos_
    if i<len(doc)-1:
        ntext = str(doc[i+1].text).lower()
        npos = doc[i+1].pos_

    is_verb = word.tag_=="VB" or (word.tag_=="VBG" and wtext not in ["serving"])

    is_instr_and_ingred_verb = wtext=="bake" or (wtext in instr_and_ingred_words and (i==0 or ( i<len(doc)-1 and npos in ["NOUN","DET","ADP","ADV"] and ntext not in ["with","for"]) or (i>0 and ptag=="RB") ) and (i>0 and ppos!="VERB" and ptag not in ["DT","JJ"]) and ntext not in ["fish","sugar"])

    is_instr_verb = wtext in instr_verbs and ((i>0 and ptext not in abstract_temps and ptext not in instr_verbs and wtext not in cookers and wtext!="grate" and word.tag_!="JJ" and ptag not in ["DT","JJ"]) or i==0)

    return (is_verb or is_instr_and_ingred_verb or is_instr_verb) and wtext not in ["herbes"]

'''
This function assumes the noun phrase text is a dobj or nsubj of an action.  If it contains a number (like "2 cups"), it probably means the actual dobj is in a future phrase with an "of" root.

In other words:
    "2 cups" => True
    "2 minutes" => False
    "the stairwell" => False
'''
def check_if_of(npt):
    probably_amt = False
    for term in str(npt).split(" "):
        if nle.is_number(term):
            probably_amt = True
    if probably_amt:
        if not any(t in npt for t in time_units):
            if any(mu in str(npt).split(" ") for mu in measurement_units) or any(nle.noun.plural(mu) in str(npt).split(" ") for mu in measurement_units):
                return True
    return False

'''
Remove stopwords from an input string.
'''
def remove_stopwords(s):
    final = ""
    doc = nlp(u''+s+'')
    for word in doc:
        if not word.is_stop:
            final += str(word.text) + " "
    return final.strip()

'''
Separates entity from quality describing entity in a noun phrase.
Example:
    "hot, shimmering olive oil" >> ("olive oil", ["hot","shimmering"])
'''
# TODO: "1-inch squares" case
def separate_entity_and_quality(np):
    np = np.replace(" - ", "-")
    qualities = []
    current_quality = ""
    entity = ""
    previous_tag = ""
    if np:
        for word in np.split(" "):
            if not is_number_or_fraction(word):
                pos = nle.sentence.tag(word)[0][1]
                if pos=="RB":
                    current_quality += word + " "
                    previous_tag = "RB"
                # Note: "slow cooker", "powdered sugar" exceptions.
                elif (pos=="JJ" and word not in ["slow","powdered"]) or pos=="VBN":
                    if previous_tag=="RB":
                        current_quality += word
                        qualities.append(current_quality)
                    else:
                        qualities.append(word)
                    current_quality = ""
                    previous_tag = "VBN/JJ"
                else: #pos=="VBG" or pos=="NN" or pos=="VBD" or pos=="NNS":
                    entity += word + " "
                    previous_tag = "VBG/NN"
    return (entity.replace(",","").strip(), qualities)

'''
Modifies string to faciliate more accurate parsing.
'''
def preprocess(s):
    final = simplify_instr_for_parser(s)
    # Note/TODO: for now, we're just removing any content in parentheses.  We may want to consider content in parentheses in the future, especially if that content contains time or temperature information.
    final = re.sub(r'\([^)]*\)', '', final)

    final = make_conj_explicit(final)

    return final

'''
Simplifies or rephrases common strings to facilitate parsing (helper for preprocess()).
'''
def simplify_instr_for_parser(s):
    final = s
    # Season can be mistaken for a noun.
    final = final.replace("Season ","Sprinkle ")
    final = final.replace(" season "," sprinkle ")

    # Need a better fix dealing with verb-prep pairs
    final = final.replace("Mix in ","Add ")
    final = final.replace(" mix in "," add ")
    final = final.replace("stir in ","add ")
    final = final.replace("Stir in ","add ")
    final = final.replace("add in ","add ")
    final = final.replace("Add in ","add ")

    final = final.replace("reduce the heat","reduce heat")
    final = final.replace("lower the heat","reduce heat")
    final = final.replace("increase the heat","increase heat")
    final = final.replace("remove from heat","turn off the heat")
    final = final.replace("Remove from heat","Turn off the heat")
    final = final.replace("remaining","")
    final = final.replace("together","")
    final = final.replace(u"°"," degrees ")
    final = final.replace("vanilla extract","vanilla")
    final = final.replace(";", ". ")

    final = final.replace("Using ","With ")
    final = final.replace(" using "," with ")
    final = final.replace("Lower ","Decrease ")
    final = final.replace(" lower "," decrease ")
    final = final.replace("Raise ","Increase ")
    final = final.replace(" raise "," increase ")

    # Not all rib roasts are prime rib, but we'll assume folks are treating themselves to the prime grade for the sake of more accurate parsing.
    final = final.replace(" rib roast"," prime rib")
    
    for mu in measurement_units:
        final = final.replace(" "+mu+" "," "+mu+" of ")
        final = final.replace(" "+nle.noun.plural(mu)+" "," "+nle.noun.plural(mu)+" of ")
    final = final.replace(" of of "," of ")

    final = final.replace(" outdoor grill "," grill ")
    for cooker in cookers:
        final = final.replace(" "+cooker+" ", " the "+cooker+" ")

    final = final.replace(" f "," Fahrenheit ")
    final = final.replace(" F "," Fahrenheit ")
    final = final.replace(" c "," Celsius ")
    final = final.replace(" C "," Celsius ")

    if final[-2:].lower()==" f":
        final = final[:-1] + "Fahrenheit"
    elif final[-2:].lower()==" c":
        final = final[:-1] + "Celsius"

    final = final.replace(" the the "," the ")
    final = final.replace(" an the "," the ")
    final = final.replace(" a the "," the ")
    return final

'''
Replaces commas used in list form with "and".

Example:
    Stir the tomato paste, oregano, the brown sugar, and onion together.
    >> Stir the tomato paste and oregano and brown sugar and onion together.
(This helps with spacy noun_chunk parsing.)
'''
def make_conj_explicit(s):
    final = ""
    final = s.replace(",", " and")
    final = final.replace("and and","and")
    return final

'''
Takes in a string (line), a list of ingredients, and the current storypoint.
Returns a set of assertions for that string.
'''
def write_recipe_instruction_assertions(line, ingredients):
    assertions = []

    inp = preprocess(line)
    vs = get_verb_substrings(inp)

    for s in vs:
        a = make_recipe_instr_assertion(get_recipe_instr_content(s))
        if a:
            assertions.append(a)

    return assertions
