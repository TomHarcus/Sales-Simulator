from transformers import AutoTokenizer
from datasets import load_dataset, DatasetDict

dataset = load_dataset("TomHarcus/sales-behaviour-classifier-dataset", split="train")

shuffled_dataset = dataset.shuffle()

train_test = shuffled_dataset.train_test_split(test_size=0.3)

train_test_valid = train_test["test"].train_test_split(test_size=0.5)

datasets = DatasetDict({
    "train": train_test["train"],
    "test": train_test_valid["test"],
    "valid": train_test_valid["train"]
})

tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize(sample):
    return tokenizer(sample["context_turns"], sample["response"], truncation=True)



def label_to_int(sample):
    label_map = {
    "WC": 0,
    "OH": 1,
    "FD": 2,
    "AN": 3
    }

    return {"labels": label_map[sample["label"]]} 

tokenized_dataset = datasets.map(tokenize, batched=True).map(label_to_int)

tokenized_dataset = tokenized_dataset.remove_columns(["label", "context_turns", "response"])

print(tokenized_dataset)
