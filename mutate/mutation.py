import rstr
import random
from nltk.corpus import wordnet

from mutate.utility import (
    calc_edit_dist,
    multi_replace_str,
    insert_line_above,
    avoid_definition
)
from mutate.c_parser import keywords, std_function


def modify_identifier(private_code, private_parse, object_features):
    if not private_parse["identifiers"]:
        return None
    original_identifier, locations = random.choice(
        list(private_parse["identifiers"].items()))
    modi_char = random.randint(0, len(original_identifier)-1)
    new_identifier = original_identifier[:modi_char] + \
        rstr.xeger(r'[A-Za-z]')+original_identifier[modi_char+1:]

    if (new_identifier in keywords) or (new_identifier in std_function) or (new_identifier in private_parse["identifiers"].keys()):
        new_identifier += rstr.xeger(r'_[A-Za-z][0-9a-zA-Z_]{1,2}')
    new_code = multi_replace_str(
        private_code, original_identifier, new_identifier, locations)

    delta_edit_dist = calc_edit_dist(
        original_identifier, new_identifier)*len(locations)

    return new_code, delta_edit_dist


def replace_identifier(private_code, private_parse, object_features):
    if not private_parse["identifiers"]:
        return None
    object_features["identifiers"].append(
        rstr.xeger(r'[A-Za-z][0-9a-zA-Z_]{3,5}'))

    new_identifier = random.choice(object_features["identifiers"])
    if (new_identifier in keywords) or (new_identifier in std_function) or (new_identifier in private_parse["identifiers"].keys()):
        new_identifier += rstr.xeger(r'_[A-Za-z][0-9a-zA-Z_]{1,5}')
    original_identifier, locations = random.choice(
        list(private_parse["identifiers"].items()))
    new_code = multi_replace_str(
        private_code, original_identifier, new_identifier, locations)

    delta_edit_dist = calc_edit_dist(
        original_identifier, new_identifier)*len(locations)

    return new_code, delta_edit_dist


def wordnet_synonym(private_code, private_parse, object_features):
    if not private_parse["identifiers"]:
        return None

    # filter out short identifier
    alter_list = list(filter(lambda x: True if(len(x[0]) > 2) else False, list(
        private_parse["identifiers"].items())))
    if not alter_list:
        return None

    original_identifier, locations = random.choice(alter_list)
    synonyms = []
    for syn in wordnet.synsets(original_identifier):
        for l in syn.lemmas():
            synonyms.append(l.name())
    if not synonyms:
        return None

    new_identifier = random.choice(list(synonyms))
    if (new_identifier in keywords) or (new_identifier in std_function) or (new_identifier in private_parse["identifiers"].keys()):
        new_identifier += rstr.xeger(r'_[A-Za-z][0-9a-zA-Z_]{1,5}')
    new_code = multi_replace_str(
        private_code, original_identifier, new_identifier, locations)

    delta_edit_dist = calc_edit_dist(
        original_identifier, new_identifier)*len(locations)

    return new_code, delta_edit_dist


def program_synonym(private_code, private_parse, object_features):
    # select all one-character identifier
    alter_list = list(filter(lambda x: True if(len(x[0]) == 1) else False, list(
        private_parse["identifiers"].items())))
    if not alter_list or len(alter_list) < 2:
        return None
    (iden_1, locs_1), (iden_2, locs_2) = random.sample(alter_list, 2)

    temp_code = multi_replace_str(
        private_code, iden_1, iden_2, locs_1)
    new_code = multi_replace_str(
        temp_code, iden_2, iden_1, locs_2)

    delta_edit_dist = len(locs_1)+len(locs_2)

    return new_code, delta_edit_dist


def int_rewrite(private_code, private_parse, object_features):
    if not private_parse["ints"]:
        return None
    # insert two random int
    object_features["ints"].append(str(random.randint(0, 32768)))
    object_features["ints"].append(str(random.randint(0, 32768)))

    new_int_1, new_int_2 = random.sample(object_features["ints"], 2)
    original_int, locations = random.choice(
        list(private_parse["ints"].items()))
    locations = [random.choice(locations)]

    pattern_switch = {
        0: "({} + {})".format(
            new_int_1, int(original_int)-int(new_int_1)),
        1: "({} - {})".format(
            int(new_int_1)+int(original_int), new_int_1),
        # 2: "{} + {} + {}".format(
        #     new_int_1, new_int_2,
        #     int(original_int)-int(new_int_1)-int(new_int_2)),
        # 3: "{} - {} - {}".format(
        #     int(original_int)+int(new_int_1)+int(new_int_2),
        #     new_int_1, new_int_2)
    }

    def select_pattern(case):
        return pattern_switch[case]

    rewrite_token = select_pattern(random.randint(0, len(pattern_switch)-1))
    new_code = multi_replace_str(
        private_code, original_int, rewrite_token, locations)

    delta_edit_dist = calc_edit_dist(
        original_int, rewrite_token)*len(locations)

    return new_code, delta_edit_dist


def int_insert_define(private_code, private_parse, object_features):
    # only insert in one place

    if not private_parse["ints"]:
        return None
    object_features["ints"].append(str(random.randint(0, 32768)))
    object_features["identifiers"].append(
        rstr.xeger(r'[A-Za-z][0-9a-zA-Z_]{3,5}'))

    new_identifier = random.choice(object_features["identifiers"])
    if (new_identifier in keywords) or (new_identifier in std_function) or (new_identifier in private_parse["identifiers"].keys()):
        new_identifier += rstr.xeger(r'_[A-Za-z][0-9a-zA-Z_]{1,5}')
    new_int = random.choice(object_features["ints"])
    original_int, locations = random.choice(
        list(private_parse["ints"].items()))
    locations = list(filter(lambda x: avoid_definition(
        private_code, private_parse["line_breaks"], [x]), locations))
    if not locations:
        return None
    the_loc = random.choice(locations)

    rewrite_token = "({} - {})".format(new_identifier, new_int)
    temp_code = multi_replace_str(
        private_code, original_int, rewrite_token, [the_loc])

    new_line = "int {} = {}; \n".format(
        new_identifier, int(new_int)+int(original_int))
    new_code = insert_line_above(
        temp_code, private_parse["line_breaks"], new_line, the_loc)

    delta_edit_dist = calc_edit_dist(
        original_int, rewrite_token)+len(new_line)

    return new_code, delta_edit_dist


def float_rewrite(private_code, private_parse, object_features):
    if not private_parse["floats"]:
        return None

    object_features["ints"].append(str(random.randint(1, 32768)))
    object_features["floats"].append(rstr.xeger(r'[0-9]{1,5}\.[0-9]{1,5}'))
    object_features["floats"].append(rstr.xeger(r'[0-9]{1,5}\.[0-9]{1,5}'))

    new_int = random.choice(object_features["ints"])
    new_float_1, new_float_2 = random.sample(object_features["floats"], 2)
    original_float, locations = random.choice(
        list(private_parse["floats"].items()))
    locations = [random.choice(locations)]

    pattern_switch = {
        0: "({} + {})".format(
            new_float_1, float(original_float)-float(new_float_1)),
        1: "({} - {})".format(
            float(new_float_1)+float(original_float), new_float_1),
        2: "({} * {})".format(
            float(original_float)/float(new_int), new_int),
        3: "({} / {})".format(
            float(original_float)*float(new_int), new_int),
        # 4: "{} + {} + {}".format(
        #     new_float_1, new_float_2,
        #     float(original_float)-float(new_float_1)-float(new_float_2)),
        # 5: "{} - {} - {}".format(
        #     float(original_float)+float(new_float_1)+float(new_float_2), new_float_1, new_float_2),
    }

    def select_pattern(case):
        return pattern_switch[case]

    rewrite_token = select_pattern(random.randint(0, len(pattern_switch)-1))
    new_code = multi_replace_str(
        private_code, original_float, rewrite_token, locations)

    delta_edit_dist = calc_edit_dist(
        original_float, rewrite_token)*len(locations)

    return new_code, delta_edit_dist


def float_insert_define(private_code, private_parse, object_features):
    # only insert in one place

    if not private_parse["floats"]:
        return None
    object_features["floats"].append(rstr.xeger(r'[0-9]{1,5}\.[0-9]{1,5}'))
    object_features["identifiers"].append(
        rstr.xeger(r'[A-Za-z][0-9a-zA-Z_]{3,5}'))

    new_identifier = random.choice(object_features["identifiers"])
    if (new_identifier in keywords) or (new_identifier in std_function) or (new_identifier in private_parse["identifiers"].keys()):
        new_identifier += rstr.xeger(r'_[A-Za-z][0-9a-zA-Z_]{1,5}')
    new_float = random.choice(object_features["floats"])
    original_float, locations = random.choice(
        list(private_parse["floats"].items()))
    the_loc = random.choice(locations)

    rewrite_token = "({} - {})".format(new_identifier, new_float)
    temp_code = multi_replace_str(
        private_code, original_float, rewrite_token, [the_loc])

    new_line = "float {} = {}; \n".format(
        new_identifier, float(new_float)+float(original_float))
    new_code = insert_line_above(
        temp_code, private_parse["line_breaks"], new_line, the_loc)

    delta_edit_dist = calc_edit_dist(
        original_float, rewrite_token)+len(new_line)

    return new_code, delta_edit_dist


def string_rewrite(private_code, private_parse, object_features):
    if not private_parse["strings"]:
        return None
    # filer out short string, which can't be splitted
    alter_list = list(filter(
        lambda x: True if (len(x[0]) > 4) and avoid_definition(
            private_code, private_parse["line_breaks"], x[1]) else False,
        list(private_parse["strings"].items())
    ))
    if not alter_list:
        return None

    original_string, locations = random.choice(alter_list)
    string_break = random.randint(2, len(original_string)-2)
    if original_string[string_break-1] == '\\':
        return None
    locations = [random.choice(locations)]

    string_1 = original_string[:string_break]+original_string[0]
    string_2 = original_string[0]+original_string[string_break:]
    # strdup may not be supported by the compiler, but this evil function was used in POJ-104/7/1075
    rewrite_token = "strcat(strdup({}), {})".format(string_1, string_2)
    new_code = multi_replace_str(
        private_code, original_string, rewrite_token, locations)

    delta_edit_dist = calc_edit_dist(
        original_string, rewrite_token)*len(locations)

    return new_code, delta_edit_dist


def string_insert_define(private_code, private_parse, object_features):
    if not private_parse["strings"]:
        return None

    # filer out short string, which can't be splitted
    alter_list = list(filter(
        lambda x: True if(len(x[0]) > 4) else False,
        list(private_parse["strings"].items())
    ))
    if not alter_list:
        return None
    original_string, locations = random.choice(alter_list)
    string_break = random.randint(2, len(original_string)-2)
    if original_string[string_break-1] == '\\':
        return None
    locations = list(filter(lambda x: avoid_definition(
        private_code, private_parse["line_breaks"], [x]), locations))
    if not locations:
        return None
    the_loc = random.choice(locations)
    if not avoid_definition(private_code, private_parse["line_breaks"], [the_loc]):
        return None

    # insert two random identifiers
    object_features["identifiers"].append(
        rstr.xeger(r'[A-Za-z][0-9a-zA-Z_]{3,5}'))
    object_features["identifiers"].append(
        rstr.xeger(r'[A-Za-z][0-9a-zA-Z_]{3,5}'))
    new_identifier_1, new_identifier_2 = random.sample(
        set(object_features["identifiers"]), 2)
    string_1 = original_string[:string_break]+original_string[0]
    string_2 = original_string[0]+original_string[string_break:]

    rewrite_token = "strcat({}, {})".format(new_identifier_1, new_identifier_2)
    temp_code = multi_replace_str(
        private_code, original_string, rewrite_token, [the_loc])

    new_line = "char {}[50] = {}; \nchar {}[50] = {}; \n".format(
        new_identifier_1, string_1,
        new_identifier_2, string_2,
    )
    new_code = insert_line_above(
        temp_code, private_parse["line_breaks"], new_line, the_loc)

    delta_edit_dist = calc_edit_dist(
        original_string, rewrite_token)+len(new_line)

    return new_code, delta_edit_dist


def single_line_insert(private_code, private_parse, object_features):
    object_features["ints"].append(str(random.randint(0, 32768)))
    object_features["floats"].append(rstr.xeger(r'[0-9]{1,5}\.[0-9]{1,5}'))
    object_features["identifiers"].append(
        rstr.xeger(r'[A-Za-z][0-9a-zA-Z_]{3,5}'))
    object_features["strings"].append(
        rstr.xeger(r'\"([0-9a-zA-Z_]{3,6}\ ){0,3}[0-9a-zA-Z_]{3,6}[\!\.:]?\"')
    )

    new_identifier = random.choice(object_features["identifiers"])
    if (new_identifier in keywords) or (new_identifier in std_function) or (new_identifier in private_parse["identifiers"].keys()):
        new_identifier += rstr.xeger(r'_[A-Za-z][0-9a-zA-Z_]{1,5}')
    new_int = random.choice(object_features["ints"])
    new_float = random.choice(object_features["floats"])
    new_string = random.choice(object_features["strings"])

    alter_locs = sum(private_parse["identifiers"].values(), [])
    alter_locs.append(0)
    insert_location = random.choice(alter_locs)

    pattern_switch = {
        0: "int {} = {};\n".format(new_identifier, new_int),
        1: "float {} = {};\n".format(new_identifier, new_float),
        2: "double {} = {};\n".format(new_identifier, new_float),
        3: "char {}[50] = {};\n".format(new_identifier, new_string),
    }

    def select_pattern(case):
        return pattern_switch[case]

    new_line = select_pattern(random.randint(0, len(pattern_switch)-1))
    new_code = insert_line_above(
        private_code, private_parse["line_breaks"], new_line, insert_location)

    delta_edit_dist = len(new_line)

    return new_code, delta_edit_dist


def multiple_line_insert(private_code, private_parse, object_features):
    # todo
    pass


mutations_list = [
    modify_identifier,
    replace_identifier, wordnet_synonym, program_synonym,
    int_rewrite, int_insert_define,
    float_rewrite, float_insert_define,
    string_rewrite, string_insert_define,
    single_line_insert,
]
