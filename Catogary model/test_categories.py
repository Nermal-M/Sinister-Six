#!/usr/bin/env python3
"""
Test script to verify category name predictions
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json
import os

def load_model(model_dir, config_path):
    """Load a BERT model and its tokenizer"""
    try:
        # Load config to get label info
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Try to load tokenizer from pretrained
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_dir)
        except:
            print(f"Using standard BERT tokenizer for {model_dir}")
            tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
        
        # Load model from the safetensors file
        model_path = os.path.join(model_dir, "model.safetensors")
        
        if os.path.exists(model_path):
            print(f"Loading model from {model_path}")
            model = AutoModelForSequenceClassification.from_pretrained(
                model_dir,
                trust_remote_code=True
            )
        else:
            print(f"Model file not found at {model_path}")
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

def main():
    # Model paths
    model1_path = r"e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model"
    config1_path = r"e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model\config.json"
    
    model2_path = r"e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model\pr"
    config2_path = r"e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model\pr\config.json"
    
    # Load both models
    print("Loading Model 1 (Category)...")
    model1, tokenizer1, config1 = load_model(model1_path, config1_path)
    
    print("Loading Model 2 (Priority)...")
    model2, tokenizer2, config2 = load_model(model2_path, config2_path)
    
    if model1 is None or model2 is None:
        print("Failed to load models")
        return
    
    # Test complaints
    test_complaints = [
        "Food quantity provided was very less compared to the price charged",
        "Seats and windows in coach are covered with dust and stains",
        "Running behind schedule since morning with frequent stops",
        "Staff used harsh language and behaved unprofessionally",
        "A suspicious person was roaming inside the coach at night"
    ]
    
    print("\n" + "="*80)
    print("COMPLAINT CATEGORY AND PRIORITY PREDICTION RESULTS")
    print("="*80)
    
    for complaint in test_complaints:
        print(f"\nComplaint: {complaint}")
        print("-" * 80)
        
        # Get predictions
        result1 = predict(model1, tokenizer1, config1, complaint)
        result2 = predict(model2, tokenizer2, config2, complaint)
        
        print(f"  ✓ Category: {result1['predicted_label']} (confidence: {result1['confidence']:.4f})")
        print(f"  ✓ Priority:  {result2['predicted_label']} (confidence: {result2['confidence']:.4f})")
        
        print(f"\n  Category Breakdown:")
        for label, score in result1['all_scores'].items():
            print(f"    {label}: {score:.4f}")
        
        print(f"\n  Priority Breakdown:")
        for label, score in result2['all_scores'].items():
            print(f"    {label}: {score:.4f}")

if __name__ == "__main__":
    main()
