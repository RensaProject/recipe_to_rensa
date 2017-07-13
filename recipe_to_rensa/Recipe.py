from rensabrain.Brain import *
import nodebox_linguistics_extended as nle
import re
from ingredparse import interpret_parsed_ingredient
from ingredparse import resolve_multiple_units

class Recipe(object):
    def __init__(self, attributes={}):
        self.name = attributes['name'] if "name" in attributes else "My Recipe"
        self.brain = attributes['brain'] if "brain" in attributes else Brain()

    def save(self,path):
        self.brain.save_brain(path)

    # Note: this will only work in simple recipes with exact ingredient amounts that do not use specific amounts of an ingredient during instruction steps.
    def substitute(self, ingredient_info, ingredient2_info):
        ingred1, measure1 = ingredient_info[0], ingredient_info[1]
        ingred2, measure2 = ingredient2_info[0], ingredient2_info[1]
        ids_to_edit = self.brain.get_assertion_ids_related_to(ingred1)
        for iden in ids_to_edit:
            a = self.brain.get_assertion_by_ID(iden)
            # Change text attribute if exists.
            if hasattr(a,"text"):
                self.brain.edit_assertion(iden,"text",a.text.replace(ingred1, ingred2).replace(measure1,measure2))
            # Change quantity for instance_of ingredient.
            if hasattr(a,"quantity"):
                parsed = resolve_multiple_units(measure2 + " flour")
                new_quantity = interpret_parsed_ingredient(parsed)[1]
                self.brain.edit_assertion(iden,"quantity",new_quantity)
            for prop, value in a.__dict__.iteritems():
                if (concept_in_assertion(iden,a,prop,value,ingred1)):
                    if isinstance(value,basestring):
                        self.brain.edit_assertion(iden,prop,ingred2)
                    elif isinstance(value,list):
                        if all(isinstance(x, basestring) for x in value):
                            self.brain.edit_assertion(iden,prop,[w.replace(ingred1, ingred2) for w in value])
                        elif all(isinstance(x, dict) for x in value):
                            new_dicts = []
                            for d in value:
                                new_dict = d.copy()
                                edit_keys = []
                                new_values = []
                                for p,v in d.iteritems():
                                    if isinstance(v,basestring) and v==ingred1:
                                        edit_keys.append(p)
                                        new_values.append(ingred2)
                                    elif isinstance(v,list) and ingred1 in v:
                                        edit_keys.append(p)
                                        new_values.append([w.replace(ingred1, ingred2) for w in v])
                                for ik,ek in enumerate(edit_keys):
                                    new_dict[ek] = new_values[ik]
                                    new_dicts.append(new_dict)
                            self.brain.edit_assertion(iden,prop,new_dicts)

    def get_ingredient_assertions(self):
        return self.brain.get_assertions_with({"relation":"instance_of","r":["ingredient"]})

    def get_ingredients(self):
        # return [(ia["r_num"][0], ia["r_unit"][0], ia["l"][0]) for ia in self.get_ingredient_assertions()]
        # TODO?
        return [(ia["quantity"], ia["l"][0]) for ia in self.get_ingredient_assertions()]

    # TODO exact vs. range
    def realize_ingredients(self):
        result = ""
        for ingred in self.get_ingredients():
            ingred_str = ""
            quantity, name = ingred[0], ingred[1]
            if quantity["type"]=="exact":
                for i, v in enumerate(quantity["values"]):
                    value = v["value"]
                    unit = v["unit"]
                    if i>0:
                        ingred_str += " + "
                    ingred_str += (value + " " + unit).strip()
            ingred_str += " "+name+"\n"
            result += ingred_str.lstrip()
        return result

    # def realize_ingredients(self):
    #     result = ""
    #     for ingred in self.get_ingredients():
    #         ingred_str = ""
    #         for i in ingred:
    #             if i!="":
    #                 ingred_str += i + " "
    #         result += ingred_str[:-1]+"\n"
    #     return result

    def get_instruction_assertions(self):
        return self.brain.get_assertions_with({"type":["recipe instruction"]})

    def realize_instructions(self):
        result = ""
        for i, instr in enumerate(self.get_instruction_assertions()):
            result += str(i+1) + ". " + realize_brain_assertion(self.brain,Assertion(instr),False) + "\n"

        # sp_list = []
        # for instr in self.get_instruction_assertions():
        #     a = Assertion(instr)
        #     sp_list.append([sp,realize_brain_assertion(self.brain,Assertion(instr),True)])

        return result

    def realize(self):
        result = self.name.upper() + "\n"
        result += "\nIngredients:\n"
        result += self.realize_ingredients()
        result += "\nInstructions:\n"
        result += self.realize_instructions()
        return result

# '''
# Realizes a set of recipe instructions that occur at the same storypoint.
# '''
# def realize_brain_assertions(brain,a,a2,isFragment):
#     result = ""
#     for a in asserts[0:-1]:
#         result+= realize_brain_assertion(brain,a,True,False) + "; "
#     result+= realize_brain_assertion(brain,a,True,True)
#     return result

'''
Realizes a recipe instruction.  This is a temporary function until the realize_simprel repository is made public.
'''
def realize_brain_assertion(brain,a,isFragment): #isSPLast
    result = ""
    adverbs,action_objects = [],[]
    main_action = ""

    if not hasattr(a,"relation") or a.relation=="action":
        if hasattr(a,"with_property"):
            result += list_words_naturally(a.with_property) + " "
        if hasattr(a,"r"):
            main_action = a.r[0]
            result += list_words_naturally(a.r)
        if hasattr(a,"action_object"):
            if any(isinstance(el, list) for el in a.action_object):
            # if a.action_object[0]:
                result += " "
                result += list_ors_naturally(a.action_object)
            else:
                result += " "
                result += list_words_naturally(a.action_object)
            # This is a list of quantities corresponding to each action_object
            if hasattr(a,"action_object_quantity"):
                measures = []
                for q in a.action_object_quantity:
                    realized_measure = ""
                    if "type" in q:
                        # TODO range case
                        if q["type"]=="exact":
                            measure = [(v["value"] + " " + v["unit"]).strip() for v in q["values"]]
                            if any(m for m in measure):
                                realized_measure = " + ".join(measure)
                        if "ingredient" in q:
                            realized_measure += " "+q["ingredient"]
                    measures.append(realized_measure)
                if any(meas for meas in measures):
                    result += " (using "
                    result += list_words_naturally(measures)
                    result += ")"

        # Get all prepositional phrases.
        preps = [(k[10:],v) for k,v in a.to_dict().items() if 'condition_' in k.lower() and k.lower()!="condition_given" and v[0]]
        for prep in preps:
            result += " "+prep[0]+" "
            result += list_clauses_naturally(brain,prep[1])
        if hasattr(a,"time_for"): #and isSPLast:
            if len(a.time_for)>1:
                result += " for " + list_words_naturally(a.time_for)
                # result += " (perform these actions for "
                # result += list_words_naturally(a.time_for)
                # result += ", respectively)"
            else:
                result += " for " + str(a.time_for[0])
        for k,v in a.to_dict().iteritems():
            if k.startswith("location_"):
                # article = ""
                # is_plural = True
                # try:
                #     article = nle.noun.article(v[0]).split(" ")[0]
                #     is_plural = nle.noun.plural(nle.noun.singular(v[0]))==v[0]
                # except:
                #     pass
                # if article == "" or is_plural:
                #     article = "the"
                # result += " " + k[9:] + " " + article + " "
                result += " " + k[9:] + " "
                result += list_words_naturally(v)
        if hasattr(a,"temperature"):
            # result += " at " + list_words_naturally(a.temperature)
            if len(a.temperature)>1:
                result += " from " + a.temperature[0]["value"] + " to " + a.temperature[1]["value"]
            else:
                if main_action in ["reduce","increase","decrease","set","preheat"]:
                    result += " to "
                elif a.temperature[0]["type"]=="specific":
                    result += " at "
                else:
                    result += " over "
                result += a.temperature[0]["value"]
                if a.temperature[0]["type"]=="abstract":
                    if hasattr(a,"action_object"):
                        if "heat" not in a.action_object:
                            result += " heat"

    # elif a.relation=="set_value":
    #     result = "set the " + a.l[0] + " to " + a.r[0]
    #     if hasattr(a,"r_unit"):
    #         result+= " " + a.r_unit[0]

    # Note/TODO: This is a temporary means of listing the property/quality of something.  Slightly problematic if we have similar nouns (e.g. brown sugar vs. white sugar).  Consider giving each an ID.
    if hasattr(a,"condition_given"):
        for c in a.condition_given:
            whole_word_idxs = [m.start() for m in re.finditer(c["l"][0], result)]
            if whole_word_idxs:
                added_length = 0
                for idx in whole_word_idxs:
                    result = result[:idx+added_length] + list_words_naturally(c["r"]) + " " + result[idx+added_length:]
                    added_length += len(list_words_naturally(c["r"]) + " ")
            else:
                base_word_idxs = [m.start() for m in re.finditer(c["l"][0].split(" ")[-1], result)]
                added_length = 0
                for idx2 in base_word_idxs:
                    result = result[:idx2+added_length] + list_words_naturally(c["r"]) + " " + result[idx2+added_length:]
                    added_length += len(list_words_naturally(c["r"]) + " ")

    # Just in case, replace multiple spaces with a single space.
    result = re.sub( '\s+', ' ', result ).strip()

    # Make result a sentence (capitalize first letter and end with terminating punctuation).
    if not isFragment and len(result)>0:
        result = result[0].upper() + result[1:] + "."
    return result

'''
Realizes a list of words in a natural format.
Examples:
 - ["one"] => "one"
 - ["one","two"] => "one and two"
 - ["one","two","three"] => "one, two, and three"
'''
def list_words_naturally(arr):
    finalString = ""
    if arr:
        for i in range(0, len(arr)):
            concept=arr[i]
            if (i<len(arr)-2):
                finalString += concept + ", "
            elif (i==len(arr)-2):
                if (len(arr)==2):
                    finalString+= concept + " and "
                else:
                    finalString += concept + ", and "
            else:
                finalString += concept
    return finalString

def list_ors_naturally(arr_of_arrs):
    finalString = ""
    if arr_of_arrs:
        for arr in arr_of_arrs:
            finalString += list_words_naturally(arr) + " or "
    return finalString[:-4]

# Uses list_words_naturally to connect assertion clauses.
# Example:
# [
    # {"l":["milk"], "relation":"has_property","r":["blue"]},
    # {"l":["sand"], "relation":"has_property","r":["coarse","irritating"]}
# ]
# =>
# The milk is blue and the sand is coarse and irritating
def list_clauses_naturally(brain, arr):
    newArr = []
    for e in arr:
        newArr.append(realize_brain_assertion(brain, Assertion(e), True))
    return list_words_naturally(newArr)
