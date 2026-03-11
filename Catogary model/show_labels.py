#!/usr/bin/env python3
"""
Script to display label information from both models
"""

import json

def show_labels():
    """Display label mappings for both models"""
    
    print("\n" + "="*60)
    print("MODEL LABEL INFORMATION")
    print("="*60)
    
    # Model 1 labels
    print("\nMODEL 1 (Root - 5 classes)")
    print("-" * 60)
    with open(r"e:\Downloads\Catogary model\config.json", 'r') as f:
        config1 = json.load(f)
    
    id2label1 = config1.get('id2label', {})
    print("Label Mappings:")
    for id_num, label_name in sorted(id2label1.items(), key=lambda x: int(x[0])):
        print(f"  ID {id_num}: {label_name}")
    
    # Model 2 labels
    print("\nMODEL 2 (PR - 3 classes)")
    print("-" * 60)
    with open(r"e:\Downloads\Catogary model\pr\config.json", 'r') as f:
        config2 = json.load(f)
    
    id2label2 = config2.get('id2label', {})
    print("Label Mappings:")
    for id_num, label_name in sorted(id2label2.items(), key=lambda x: int(x[0])):
        print(f"  ID {id_num}: {label_name}")
    
    print("\n" + "="*60)
    print("NOTE: The labels are generic (LABEL_0, LABEL_1, etc.)")
    print("The actual meaning of these labels depends on your training data.")
    print("="*60 + "\n")

if __name__ == "__main__":
    show_labels()
