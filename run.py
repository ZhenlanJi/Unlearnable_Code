import os
import random
import argparse
import mutate.main as mt
from mutate.init import init_target_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        "-dataset",
        help="dataset path",
        type=str,
        default="",
    )
    parser.add_argument(
        "--output",
        "-output",
        help="output path",
        type=str,
        default="",
    )
    parser.add_argument(
        "--cuda",
        "-cuda",
        help="cuda device",
        type=str,
        default="0",
    )
    parser.add_argument(
        "--class_mode",
        "-class_mode",
        help="select class mode",
        type=str,
        default="farthest",
    )
    parser.add_argument(
        "--selected_num",
        "-selected_num",
        help="the number of mutated programs in each class",
        type=int,
        default="200",
    )
    parser.add_argument(
        "--object_nearest",
        "-object_nearest",
        help="whether select object nearest",
        action='store_true'
    )
    parser.add_argument(
        "--dist_ratio",
        "-dist_ratio",
        help="ratio of two distance, when it is None, \
        only try to minimize the distance to object, \
        when it is 0, only try to maximize the distance to private code",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--epoch",
        "-epoch",
        help="epoch of mutation",
        type=int,
        default=15,
    )
    parser.add_argument(
        "--feature_num",
        "-feature_num",
        help="the number of features extracted from object code",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--random_max_try",
        "-random_max_try",
        help="max try times of random mutation",
        type=int,
        default=256,
    )
    args = parser.parse_args()
    print("Running parameters %s", args)

    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"] = args.cuda
    init_target_model()
    extensions = ('.txt')

    for root, dirs, _ in os.walk(args.dataset):
        for dir in dirs:
            alter_list = []
            new_path = os.path.join(root, dir)
            for subdir, _, files in os.walk(new_path):
                for file in files:
                    ext = os.path.splitext(file)[-1].lower()
                    if ext in extensions:
                        alter_list.append(os.path.join(subdir, file))
            selected_files = random.sample(alter_list, args.selected_num)
            for s in selected_files:
                mt.mutate(s, args.dataset, os.path.join(args.output, "mutated", dir),
                          os.path.join(args.output, "log"), class_mode=args.class_mode,
                          object_nearest=args.object_nearest, dist_ratio=args.dist_ratio,
                          epoch=args.epoch, feature_num=args.feature_num,
                          random_max_try=args.random_max_try)


if __name__ == "__main__":
    main()
