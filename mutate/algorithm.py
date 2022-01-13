import operator
import rstr

from mutate.utility import *
from mutate.mutation import *
from mutate.c_parser import parsing


def select_class(private_code, private_class, dataset, mode="random", sample_num=5):
    # mode= random, nearest, farthest
    alter_list = []
    codes_list = [private_code, ]
    extensions = ('.txt')
    if mode == "random":
        object_folder = os.path.join(
            dataset,
            str(random.choice(
                [i for i in range(1, 105) if i not in [int(private_class)]]))
        )
        return object_folder

    for root, dirs, _ in os.walk(dataset):
        for dir in dirs:
            if int(dir) == int(private_class):
                continue
            alter_list = []
            new_path = os.path.join(root, dir)
            for subdir, _, files in os.walk(new_path):
                for file in files:
                    ext = os.path.splitext(file)[-1].lower()
                    if ext in extensions:
                        alter_list.append(os.path.join(subdir, file))
            selected_files = random.sample(alter_list, sample_num)
            for file in selected_files:
                temp_file = os.path.join(root, file)
                alter_list.append(temp_file)
                temp_code = read_file(temp_file)
                codes_list.append(temp_code)

    embs_list = get_multi_cls_embeddings(codes_list)
    private_emb = embs_list[0].reshape(1, -1)

    dists_list = (torch.cdist(private_emb, embs_list[1:], p=2)
                  ).reshape(-1).tolist()
    avg_dists_list = [sum(dists_list[i:i+sample_num])/sample_num
                      for i in range(0, len(dists_list), sample_num)]
    if mode == "nearest":
        origin_dist = min(avg_dists_list)
    elif mode == "farthest":
        origin_dist = max(avg_dists_list)

    selected_class = avg_dists_list.index(origin_dist)+1
    if selected_class >= int(private_class):
        selected_class += 1
    object_folder = os.path.join(
        dataset,
        str(selected_class)
    )
    return object_folder


def select_object(private_code, object_folder, nearest=False):
    # when nearest is True, select the nearest object, else select the farthest
    alter_list = []
    codes_list = [private_code, ]
    extensions = ('.txt')

    for subdir, dirs, files in os.walk(object_folder):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if ext in extensions:
                temp_file = os.path.join(subdir, file)
                alter_list.append(temp_file)
                temp_code = read_file(temp_file)
                codes_list.append(temp_code)
    embs_list = get_multi_cls_embeddings(codes_list)
    private_emb = embs_list[0].reshape(1, -1)

    dists_list = (torch.cdist(private_emb, embs_list[1:], p=2)
                  ).reshape(-1).tolist()
    if nearest:
        origin_dist = min(dists_list)
    else:
        origin_dist = max(dists_list)
    selected_index = dists_list.index(origin_dist)
    object_file = alter_list[selected_index]
    object_code = codes_list[selected_index+1]
    object_emb = embs_list[selected_index+1].reshape(1, -1)
    return origin_dist, private_emb, object_emb, object_file, object_code


def extract_feature(object_code, object_emb, feature_num, repeat_time=10):
    # select top feature_num% important token as the feature
    features = {
        "strings": [],
        "ints": [],
        "floats": [],
        "identifiers": []
    }

    features_list = []
    delta_edit_dists = []
    mutated_codes = []
    parse_res = parsing(object_code)

    def get_mutate(token, locations, new_token):
        mutate_code = multi_replace_str(
            object_code, token, new_token, locations)
        delta_edit_dist = calc_edit_dist(
            token, new_token)
        return mutate_code, delta_edit_dist

    for token, locations in parse_res["identifiers"].items():
        if len(features_list) > 50:
            break
        max_len = len(token)+2
        # to filter out all meaningless identifiers
        if len(token) > 1:
            # repeat repeat_time times to reduce random
            for _ in range(repeat_time):
                new_token = rstr.xeger(
                    r'[A-Za-z][0-9a-zA-Z_]{0,20}')[:max_len]
                temp_mutated_code, temp_delta_edit_dist = get_mutate(
                    token, locations, new_token)
                delta_edit_dists.append(temp_delta_edit_dist)
                mutated_codes.append(temp_mutated_code)
            features_list.append(("identifiers", token))

    for token, locations in parse_res["strings"].items():
        if len(features_list) > 64:
            break
        # to filter out all meaningless strings
        if len(token) > 5:
            max_len = len(token)
            # repeat repeat_time times to reduce random
            for _ in range(repeat_time):
                new_token = '"' + \
                    rstr.xeger(r'[0-9a-zA-Z_\ ]{1,20}')[:max_len]+'"'
                temp_mutated_code, temp_delta_edit_dist = get_mutate(
                    token, locations, new_token)
                delta_edit_dists.append(temp_delta_edit_dist)
                mutated_codes.append(temp_mutated_code)
            features_list.append(("strings", token))

    for token, locations in parse_res["ints"].items():
        if len(features_list) > 72:
            break
        max_len = len(token)+2
        # to filter out all meaningless int
        if len(token) > 1:
            # repeat repeat_time times to reduce random
            for _ in range(repeat_time):
                new_token = rstr.xeger(r'[1-9]{0,20}')[:max_len]
                temp_mutated_code, temp_delta_edit_dist = get_mutate(
                    token, locations, new_token)
                delta_edit_dists.append(temp_delta_edit_dist)
                mutated_codes.append(temp_mutated_code)
            features_list.append(("ints", token))

    for token, locations in parse_res["floats"].items():
        if len(features_list) > 72:
            break
        max_len = len(token)+2
        # to filter out all meaningless float
        if len(token) > 2:
            # repeat repeat_time times to reduce random
            for _ in range(repeat_time):
                new_token = rstr.xeger(
                    r'[0-9]{1,10}\.[0-9]{1,10}')[:max_len]
                temp_mutated_code, temp_delta_edit_dist = get_mutate(
                    token, locations, new_token)
                delta_edit_dists.append(temp_delta_edit_dist)
                mutated_codes.append(temp_mutated_code)
            features_list.append(("floats", token))

    if not mutated_codes:
        return features
    embs_list = get_multi_cls_embeddings(mutated_codes)
    dists_list = (torch.cdist(object_emb, embs_list[1:], p=2)
                  ).reshape(-1).tolist()
    gradients_list = [calc_gradient(i, j)
                      for i, j in zip(dists_list, delta_edit_dists)]
    sum_gradients_list = [sum(gradients_list[i:i+repeat_time])
                          for i in range(0, len(gradients_list), repeat_time)]
    features_dict = {i: j for i, j in zip(features_list, sum_gradients_list)}

    sorted_features = sorted(
        features_dict.items(), key=operator.itemgetter(1), reverse=True)
    extracted_token = sorted_features[:int(feature_num*len(sorted_features))]
    for s in extracted_token:
        token_cls = s[0][0]
        token_val = s[0][1]
        if token_cls == "strings":
            features["strings"].append(token_val)
        elif token_cls == "ints":
            features["ints"].append(token_val)
        elif token_cls == "floats":
            features["floats"].append(token_val)
        elif token_cls == "identifiers":
            features["identifiers"].append(token_val)

    return features


def random_mutate(origin_dist, object_dist, object_emb, private_emb, interm_code,
                  object_features, max_try, dist_ratio=1.0):
    interm_parse = parsing(interm_code)

    batch_set = 4
    decay_rate = 2
    epsi = 1.0
    best_gradient = 0
    best_ori_dist = 0
    best_obj_dist = 0
    best_code = ""
    best_method = mutations_list[0].__name__

    # ε-Greedy Algorithm
    for _ in range(batch_set):
        mutated_codes = []
        selected_methods = []
        delta_edit_dists = []

        for i in range(int(max_try/batch_set)):
            while True:
                if random.random() < epsi:
                    selected_method = random.choice(mutations_list)
                    temp_ret = selected_method(
                        interm_code, interm_parse, object_features)
                else:
                    selected_method = [
                        m for m in mutations_list if m.__name__ == best_method][0]
                    temp_ret = selected_method(
                        interm_code, interm_parse, object_features)
                if temp_ret is not None:
                    mutate_code, delta_edit_dist = temp_ret
                    mutated_codes.append(mutate_code)
                    selected_methods.append((i, selected_method.__name__))
                    delta_edit_dists.append(delta_edit_dist)
                    break

        embs_list = get_multi_cls_embeddings(mutated_codes)
        origin_dists_list = (torch.cdist(private_emb, embs_list, p=2)
                             ).reshape(-1).tolist()
        object_dists_list = (torch.cdist(object_emb, embs_list, p=2)
                             ).reshape(-1).tolist()
        if dist_ratio == None:
            delta_dists_list = [(object_dist-x) for x in origin_dists_list]
        else:
            delta_dists_list = [(x-origin_dist)+dist_ratio*(object_dist-y)
                                for x, y in zip(origin_dists_list, object_dists_list)]

        gradients_list = [calc_gradient(i, j)
                          for i, j in zip(delta_dists_list, delta_edit_dists)]
        res_dict = {i: j for i, j in zip(selected_methods, gradients_list)}

        selected_attempt = max(res_dict, key=res_dict.get)
        if res_dict[selected_attempt] > best_gradient:
            best_gradient = res_dict[selected_attempt]
            best_ori_dist = origin_dists_list[selected_attempt[0]]
            best_obj_dist = object_dists_list[selected_attempt[0]]
            best_code = mutated_codes[selected_attempt[0]]
            best_method = selected_attempt[1]
        epsi = epsi/decay_rate

    # selected_method_name, mutated_code, gradient, new_dist_to_origin, new_dist_to_object
    return best_method, best_code, best_gradient, best_ori_dist, best_obj_dist
