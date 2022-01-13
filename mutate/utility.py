import numpy as np
import re
import torch
import os
from transformers import Trainer
from torch.utils.data import DataLoader

import mutate.init as init


class Emb_Dataset(torch.utils.data.Dataset):
    def __init__(self, encodings):
        self.encodings = encodings

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx])
                for key, val in self.encodings.items()}
        return item

    def __len__(self):
        return len(self.encodings["input_ids"])


def comment_remover(code):
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " "  # note: a space and not an empty string
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, code)


def split_code_line(code):
    line_matcher = re.compile('(?:"[^"]*"|.)+')
    return line_matcher.findall(code)


def read_file(file_name):
    with open(file_name, "r", errors="ignore") as f:
        code = f.read()
    code = comment_remover(code)
    return code


def is_float(x):
    try:
        a = float(x)
    except (TypeError, ValueError):
        return False
    else:
        return True


def is_int(x):
    try:
        a = float(x)
        b = int(a)
    except (TypeError, ValueError):
        return False
    else:
        return a == b and (x.isdigit())


def multi_replace_str(code, origin_token, new_token, locations):
    start = 0
    code_list = []
    token_len = len(origin_token)
    for l in locations:
        code_list.append(code[start:l])
        start = l+token_len
    code_list.append(code[start:])
    new_code = new_token.join(code_list)
    return new_code


def avoid_definition(code, line_breaks, token_locations):
    for t in token_locations:
        all_lb = [i for i in line_breaks if i < t]
        if not all_lb:
            lb = -1
        else:
            lb = max(all_lb)
        this_line = code[lb+1:t]
        if "char " in this_line:
            return False
    return True


def insert_line_above(code, line_breaks, line, token_location):
    # need to process one-line loop without brace, which is a tricky task
    avoid_keywords = ("else")
    line_breaks.reverse()
    insert_loc = 0

    for index, lb in enumerate(line_breaks):
        if lb < token_location:
            this_line = code[lb+1:token_location]
            if this_line.strip() and (this_line.strip())[0] == '{':
                insert_loc = lb+this_line.find('{')+2
                break
            else:
                if index == len(line_breaks)-1:
                    above_line = code[:lb]
                else:
                    above_line = code[line_breaks[index+1]+1:lb]
                if (above_line.strip()).endswith(('{', ';', '}')) and not code[lb+1:].strip().startswith(avoid_keywords):
                    insert_loc = lb+1
                    break
                else:
                    continue
    new_code = code[:insert_loc]+line+code[insert_loc:]
    return new_code


def get_multi_cls_embeddings(codes_list):
    clean_codes = list(map(
        lambda x: ' '.join([line.strip()for line in split_code_line(x)]),
        codes_list
    ))
    encodings = init.tokenizer(
        clean_codes,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    dataset = Emb_Dataset(encodings)
    test_loader = DataLoader(dataset, batch_size=64, shuffle=False)

    trainer = Trainer(
        model=init.model,
    )
    res = trainer.prediction_loop(test_loader, description="prediction")

    return torch.from_numpy(res.predictions[0][:, 0, :])


def calc_edit_dist(s1, s2):
    if len(s1) < len(s2):
        return calc_edit_dist(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return float(previous_row[-1])


def calc_gradient(delta_emb_dist, delta_edit_dist):
    if delta_edit_dist != 0:
        gradient = delta_emb_dist/delta_edit_dist
    else:
        gradient = 0
    return gradient
