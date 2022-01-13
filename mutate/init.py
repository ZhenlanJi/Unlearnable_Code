from transformers import (
    RobertaTokenizer,
    RobertaModel,
)


def init_target_model():
    global tokenizer, model

    tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
    model = RobertaModel.from_pretrained("microsoft/codebert-base")

    return

