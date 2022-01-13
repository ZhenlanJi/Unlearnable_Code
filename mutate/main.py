import argparse
import os
import logging
import pandas as pd

from mutate.utility import read_file
from mutate.algorithm import (
    select_class,
    select_object,
    extract_feature,
    random_mutate
)


def mutate(private_file, dataset, output_folder, log_folder, class_mode="random",
           object_nearest=False, dist_ratio=1, epoch=15, feature_num=0.5, random_max_try=512, ):
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    logging.basicConfig(filename=os.path.join(log_folder, "all_logs.log"),
                        format='%(asctime)s-%(levelname)s-%(message)s',
                        filemode='a')
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    try:
        private_code = read_file(private_file)
    except IOError:
        print("Could not read file:", private_file)
    logs = pd.DataFrame(
        columns=['selected_method', 'gradient', "origin_dist", "object_dist"])

    private_class = private_file.split('.')[0].split('/')[-2]
    # mode= random, nearest, farthest
    object_folder = select_class(
        private_code, private_class, dataset, mode=class_mode)
    # when object_nearest is True, select the nearest object, else select the farthest
    object_dist, private_emb, object_emb, object_file, object_code = select_object(
        private_code, object_folder, object_nearest)
    logger.critical(
        f"{private_file} is mutated by object folder: {object_file}")
    object_features = extract_feature(object_code, object_emb, feature_num)
    interm_code = private_code

    new_file_name = ('_'.join(private_file.split('/')[-2:])).split('.')[0]
    origin_dist = 0

    for index in range(epoch):
        selected_method, temp_code, temp_gradient, temp_ori_dist, temp_obj_dist = random_mutate(
            origin_dist, object_dist, object_emb, private_emb, interm_code,
            object_features, random_max_try, dist_ratio)
        if temp_gradient > 0:
            interm_code = temp_code
            origin_dist = temp_ori_dist
            object_dist = temp_obj_dist
            logs = logs.append({'selected_method': selected_method,
                                'gradient': temp_gradient,
                                "origin_dist": origin_dist,
                                "object_dist": object_dist}, ignore_index=True)
        else:
            logs = logs.append({'selected_method': "None",
                                'gradient': 0.0,
                                "origin_dist": origin_dist,
                                "object_dist": object_dist}, ignore_index=True)

    mutate_code = interm_code
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    with open(os.path.join(output_folder, new_file_name+".txt"), "w") as fout:
        fout.write(mutate_code)
    log_path = os.path.join(log_folder, new_file_name+".csv")
    logs.to_csv(log_path, index=False)
    logger.critical("Done!")
