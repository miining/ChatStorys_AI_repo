import os
import torch
import pandas as pd
import numpy as np
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.preprocessing import LabelEncoder
from datasets import Dataset
import argparse

def compute_metrics(pred):
    labels = pred.label_ids
    preds = np.argmax(pred.predictions, axis=1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='weighted')
    acc = accuracy_score(labels, preds)
    
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, default="monologg/koelectra-base-v3-discriminator")
    parser.add_argument("--train_file", type=str, default="data/train.csv")
    parser.add_argument("--validation_file", type=str, default="data/val.csv")
    parser.add_argument("--output_dir", type=str, default="outputs/koelectra_emotion")
    parser.add_argument("--num_labels", type=int, default=6)
    parser.add_argument("--learning_rate", type=float, default=2e-5)
    parser.add_argument("--per_device_train_batch_size", type=int, default=16)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=32)
    parser.add_argument("--num_train_epochs", type=int, default=5)
    parser.add_argument("--logging_steps", type=int, default=100)
    parser.add_argument("--save_steps", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    # Set seed
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name_or_path,
        num_labels=args.num_labels,
        problem_type="single_label_classification",
        max_length=512
    )

    # Load and preprocess data
    train_df = pd.read_csv(args.train_file)
    val_df = pd.read_csv(args.validation_file)

    # Initialize LabelEncoder
    label_encoder = LabelEncoder()
    
    # Fit and transform labels
    train_labels = label_encoder.fit_transform(train_df['emotion'])
    val_labels = label_encoder.transform(val_df['emotion'])

    # Tokenize texts
    def tokenize_function(examples):
        return tokenizer(examples['text'], padding="max_length", truncation=True, max_length=512)

    # Create datasets
    train_dataset = Dataset.from_dict({
        'text': train_df['content'].tolist(),
        'labels': train_labels.tolist()
    })
    val_dataset = Dataset.from_dict({
        'text': val_df['content'].tolist(),
        'labels': val_labels.tolist()
    })

    # Tokenize datasets
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)

    # Set format for PyTorch
    train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])
    val_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        num_train_epochs=args.num_train_epochs,
        weight_decay=0.01,
        evaluation_strategy="steps",
        eval_steps=500,
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=3,
        remove_unused_columns=False,
    )

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )

    # Train the model
    trainer.train()

    # Save the model and label encoder
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    # Save label encoder classes
    np.save(os.path.join(args.output_dir, 'label_classes.npy'), label_encoder.classes_)

if __name__ == "__main__":
    main() 