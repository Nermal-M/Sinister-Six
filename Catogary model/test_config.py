#!/usr/bin/env python3
"""
Simple test to verify predictions return category names
"""

import json
import os

# Test config loading
config_path = r"e:\Downloads\complaint-system-master\complaint-system-master\public\Catogary model\config.json"

print("Testing config loading and label mapping...\n")

with open(config_path, 'r') as f:
    config = json.load(f)

id2label = config.get('id2label', {})
print("Loaded id2label mapping from config:")
print(id2label)

print("\n" + "="*60)
print("Example: Mapping predicted class indices to labels")
print("="*60)

# Simulate predictions
test_classes = [0, 1, 2, 3, 4]

for predicted_class in test_classes:
    predicted_label = id2label.get(str(predicted_class), f"LABEL_{predicted_class}")
    print(f"Class {predicted_class} → Label: {predicted_label}")

print("\n" + "="*60)
print("RESULT: If all above show category names (Food, Cleanliness,")
print("Delay, Staff, Safety), then the mapping is working correctly!")
print("="*60)
