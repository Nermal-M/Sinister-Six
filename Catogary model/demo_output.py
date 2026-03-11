#!/usr/bin/env python3
"""
Demonstration script showing category name predictions
"""

import json

def demonstrate_prediction():
    """Show how the prediction mapping works"""
    
    # Load config
    with open(r'e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model\config.json', 'r') as f:
        config = json.load(f)
    
    with open(r'e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model\pr\config.json', 'r') as f:
        config_pr = json.load(f)
    
    # Get id2label mappings
    id2label = config.get('id2label', {})
    id2label_pr = config_pr.get('id2label', {})
    
    # Example predictions (simulated)
    test_cases = [
        (0, 0, "Food quality was poor and quantity was very less"),
        (1, 0, "Seats and windows are covered with dust and stains"),
        (2, 2, "Running behind schedule by 3 hours"),
        (3, 0, "Staff behaved rudely and unprofessionally"),
        (4, 1, "A suspicious person was roaming at night"),
    ]
    
    print("\n" + "="*80)
    print("COMPLAINT PREDICTION OUTPUT WITH CATEGORY NAMES")
    print("="*80)
    
    for predicted_class, priority_class, complaint_text in test_cases:
        category_name = id2label.get(str(predicted_class), f"LABEL_{predicted_class}")
        priority_name = id2label_pr.get(str(priority_class), f"LABEL_{priority_class}")
        
        print(f"\nComplaint: {complaint_text}")
        print("-" * 80)
        print(f"  ✓ Predicted Category: {category_name}")
        print(f"  ✓ Predicted Priority: {priority_name}")

if __name__ == "__main__":
    demonstrate_prediction()
