# Unlearnable_Code

This repository belongs to our publication:
> Unlearnable Examples: Protecting Open-Source Software from Unauthorized Neural Code Learning

You can find the code for our paper in this repository.

## Introduction

We provide approaches for protecting open-source software from unauthorized neural code learning via unlearnable examples for the first time. Our proposed technique applies a set of lightweight transformations toward a program before it is open-source released. When these transformed programs are used to train models, they mislead the model into learning the unnecessary knowledge of programs, then fail the model to complete original programs. The transformation methods are sophisticatedly designed in such a way that they do not impair the general readability of protected programs, nor do they entail a huge cost. We focus on code autocompletion as a representative downstream task of unauthorized neural code learning. We demonstrate highly encouraging and cost-effective protection against neural code autocompletion.

In summary, we make the following contributions:
* Conceptually, we advocate for a new focus on protecting software against unauthorized neural code learning, a growing concern in the open-source community.
* Technically, we propose a set of lightweight transformations to transform software in a semantics- and readability-preserving manner. The optimal transformation sequence toward a program is determined using multi-armed bandits.
* We demonstrate empirically that transformed programs effectively mislead unauthorized neural code autocompletion with negligible cost.

## Dependency

```
rstr
numpy
pandas
nltk
torch
transformers
```

## Usage
```
python run.py\
    --dataset=<path of POJ-104 or other dataset>\
    --output=<path of output folder>\

# see more details by using --help
```