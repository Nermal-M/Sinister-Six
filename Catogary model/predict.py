#!/usr/bin/env python3
"""
Script to make predictions using two BERT models
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, BertTokenizer
from safetensors.torch import load_file
import json
import os

def load_model(model_dir, config_path):
    """Load a BERT model and its tokenizer"""
    try:
        # Load config to get label info
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Try to load tokenizer from pretrained (uses bert-base-uncased by default)
        # Since we don't have tokenizer files, we'll use the standard BERT tokenizer
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_dir)
        except:
            # Fallback to standard BERT tokenizer
            print(f"  Using standard BERT tokenizer for {model_dir}")
            tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        
        # Load model from the safetensors file
        model_path = os.path.join(model_dir, "model.safetensors")
        
        if os.path.exists(model_path):
            print(f"  Loading model from {model_path}")
            model = AutoModelForSequenceClassification.from_pretrained(
                model_dir,
                trust_remote_code=True
            )
        else:
            print(f"  Model file not found at {model_path}")
            return None, None, None
        
        return model, tokenizer, config
    except Exception as e:
        print(f"Error loading model from {model_dir}: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def predict(model, tokenizer, config, text):
    """Make prediction on input text"""
    # Tokenize input
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    
    # Get predictions
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get probabilities
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1)
    predicted_class = torch.argmax(probabilities, dim=1).item()
    
    # Get label name
    id2label = config.get('id2label', {})
    predicted_label = id2label.get(str(predicted_class), f"LABEL_{predicted_class}")
    
    # Get confidence scores
    scores = probabilities[0].tolist()
    
    return {
        'predicted_class': predicted_class,
        'predicted_label': predicted_label,
        'confidence': scores[predicted_class],
        'all_scores': {id2label.get(str(i), f"LABEL_{i}"): score for i, score in enumerate(scores)}
    }

def export_predictions(predictions):
    """Export predictions to CSV file"""
    import csv
    from datetime import datetime
    
    if not predictions:
        print("No predictions to export yet.\n")
        return
    
    filename = f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Input Text',
                'Model 1 Predicted Label',
                'Model 1 Confidence',
                'Model 1 All Scores',
                'Model 2 Predicted Label',
                'Model 2 Confidence',
                'Model 2 All Scores'
            ])
            
            # Write predictions
            for pred in predictions:
                model1_scores_str = ' | '.join([f"{k}:{v:.4f}" for k, v in pred['model1_scores'].items()])
                model2_scores_str = ' | '.join([f"{k}:{v:.4f}" for k, v in pred['model2_scores'].items()])
                
                writer.writerow([
                    pred['input'],
                    pred['model1_label'],
                    f"{pred['model1_confidence']:.4f}",
                    model1_scores_str,
                    pred['model2_label'],
                    f"{pred['model2_confidence']:.4f}",
                    model2_scores_str
                ])
        
        print(f"✓ Predictions exported to {filename}\n")
    except Exception as e:
        print(f"Error exporting predictions: {e}\n")

def main():
    # Model paths
    model1_path = r"e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model"  # Root model
    config1_path = r"e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model\config.json"
    
    model2_path = r"e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model\pr"  # PR model
    config2_path = r"e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model\pr\config.json"
    
    # Load both models
    print("Loading Model 1 (Root)...")
    model1, tokenizer1, config1 = load_model(model1_path, config1_path)
    
    print("Loading Model 2 (PR)...")
    model2, tokenizer2, config2 = load_model(model2_path, config2_path)
    
    if model1 is None or model2 is None:
        print("Failed to load models")
        return
    
    print("\n" + "="*60)
    print("BERT Model Prediction Interface")
    print("="*60)
    print("\nBoth models loaded successfully!")
    print("Model 1 (Root): Predicts Complaint Category")
    print("  Categories: Food, Cleanliness, Delay, Staff, Safety")
    print("Model 2 (PR): Predicts Priority Level")
    print("  Priority Levels: Medium, High, Low")
    print("\nEnter text to get predictions from both models.")
    print("Commands: 'quit'/'exit'/'q' to exit, 'export' to save results to CSV\n")
    
    predictions = []  # Store all predictions
    
    while True:
        user_input = input("Enter text: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Exiting...")
            break
        
        if user_input.lower() == 'export':
            export_predictions(predictions)
            continue
        
        if not user_input:
            print("Please enter some text.\n")
            continue
        
        # Get predictions from both models
        print("\n" + "-"*60)
        print("INPUT:", user_input)
        print("-"*60)
        
        # Model 1 prediction
        print("\nMODEL 1 (Category Classification):")
        result1 = predict(model1, tokenizer1, config1, user_input)
        print(f"  ✓ Predicted Category: {result1['predicted_label']}")
        print(f"  Confidence: {result1['confidence']:.4f}")
        print("  Category Scores:")
        for label, score in result1['all_scores'].items():
            print(f"    {label}: {score:.4f}")
        
        # Model 2 prediction
        print("\nMODEL 2 (Priority Classification):")
        result2 = predict(model2, tokenizer2, config2, user_input)
        print(f"  ✓ Predicted Priority: {result2['predicted_label']}")
        print(f"  Confidence: {result2['confidence']:.4f}")
        print("  Priority Scores:")
        for label, score in result2['all_scores'].items():
            print(f"    {label}: {score:.4f}")
        
        # Store prediction
        predictions.append({
            'input': user_input,
            'model1_label': result1['predicted_label'],
            'model1_confidence': result1['confidence'],
            'model1_scores': result1['all_scores'],
            'model2_label': result2['predicted_label'],
            'model2_confidence': result2['confidence'],
            'model2_scores': result2['all_scores']
        })
        
        print()

if __name__ == "__main__":
    main()
