#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API for Railway Complaint Classification
Provides endpoints to classify complaints by category and priority
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json
import os
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import uuid
import hashlib

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

@app.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response, 200

@app.after_request
def add_cors_headers(response):
    """Add CORS headers to every response"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

# MongoDB Connection
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "railway_complaints_db"
mongo_client = None
db = None

# Global model variables
model1 = None
tokenizer1 = None
config1 = None
model2 = None
tokenizer2 = None
config2 = None

# Category to Department Mapping
CATEGORY_TO_DEPARTMENT = {
    'Cleanliness': 'Cleanliness',
    'Delay': 'Delay',
    'Food': 'Food',
    'Safety': 'Safety & Security',
    'Staff': 'Staff',
    'Lost/Theft': 'Lost/Theft'
}

def get_department_for_category(category):
    """Get department name for a complaint category"""
    return CATEGORY_TO_DEPARTMENT.get(category, 'General Complaints Division')

def create_notification(complaint_id, category, priority, user_email, complaint_text):
    """Create a notification for the respective department"""
    try:
        department = get_department_for_category(category)
        
        notification = {
            'complaint_id': complaint_id,
            'department': department,
            'category': category,
            'priority': priority,
            'user_email': user_email,
            'complaint_text': complaint_text[:200] + '...' if len(complaint_text) > 200 else complaint_text,
            'is_read': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = db.notifications.insert_one(notification)
        print(f"✓ Notification created for {department} (Complaint: {complaint_id})")
        return result.inserted_id
        
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None

def create_theft_lost_notification(report_id, item_type, item_description, user_email, user_name):
    """Create a notification for theft/lost item report"""
    try:
        department = 'Lost/Theft'
        
        notification = {
            'report_id': report_id,
            'complaint_id': report_id,  # For compatibility with existing notification system
            'department': department,
            'category': 'Lost/Theft',
            'priority': 'High',
            'user_email': user_email,
            'complaint_text': f'{user_name} reported a {item_type}: {item_description[:100]}...',
            'is_read': False,
            'notification_type': 'theft_lost',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = db.notifications.insert_one(notification)
        print(f"✓ Theft/Lost notification created for {department} (Report: {report_id})")
        return result.inserted_id
        
    except Exception as e:
        print(f"Error creating theft/lost notification: {e}")
        return None

def init_mongodb():
    """Initialize MongoDB connection and create collections"""
    global mongo_client, db
    try:
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client[DB_NAME]
        
        # Test connection
        mongo_client.admin.command('ping')
        print("✓ Connected to MongoDB successfully!")
        
        # Create collections if they don't exist
        create_collections()
        
        return True
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return False

def create_collections():
    """Create required collections and indexes"""
    try:
        # Users collection
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
            db.users.create_index('email', unique=True)
            print("✓ Created 'users' collection")
        
        # Complaints collection
        if 'complaints' not in db.list_collection_names():
            db.create_collection('complaints')
            db.complaints.create_index('complaint_id', unique=True)
            db.complaints.create_index('user_email')
            db.complaints.create_index('created_at')
            print("✓ Created 'complaints' collection")
        
        # Theft/Lost Items collection
        if 'theft_lost_reports' not in db.list_collection_names():
            db.create_collection('theft_lost_reports')
            db.theft_lost_reports.create_index('report_id', unique=True)
            db.theft_lost_reports.create_index('email')
            db.theft_lost_reports.create_index('phone')
            db.theft_lost_reports.create_index('created_at')
            print("✓ Created 'theft_lost_reports' collection")
        
        # Staff collection
        if 'staff' not in db.list_collection_names():
            db.create_collection('staff')
            db.staff.create_index('emp_id', unique=True)
            db.staff.create_index('email', unique=True)
            print("✓ Created 'staff' collection")
        
        # Notifications collection
        if 'notifications' not in db.list_collection_names():
            db.create_collection('notifications')
            db.notifications.create_index('department')
            db.notifications.create_index('created_at')
            db.notifications.create_index('is_read')
            print("✓ Created 'notifications' collection")
        
        # Create sample data if collections are empty
        if db.users.count_documents({}) == 0:
            create_sample_data()
        
    except Exception as e:
        print(f"Error creating collections: {e}")

def create_sample_data():
    """Create sample users and complaints for testing"""
    try:
        # Sample users
        sample_users = [
            {
                'email': 'passenger@example.com',
                'password': hashlib.sha256('password123'.encode()).hexdigest(),
                'name': 'John Passenger',
                'role': 'passenger',
                'phone': '9876543210',
                'created_at': datetime.now()
            },
            {
                'email': 'user@example.com',
                'password': hashlib.sha256('user123'.encode()).hexdigest(),
                'name': 'Jane User',
                'role': 'passenger',
                'phone': '9876543211',
                'created_at': datetime.now()
            }
        ]
        db.users.insert_many(sample_users)
        print("✓ Sample users created")
        
        # Sample staff
        sample_staff = [
            {
                'emp_id': 'EMP001',
                'email': 'staff@railway.com',
                'password': hashlib.sha256('staff123'.encode()).hexdigest(),
                'name': 'Staff Member',
                'department': 'Complaints Division',
                'created_at': datetime.now()
            }
        ]
        db.staff.insert_many(sample_staff)
        print("✓ Sample staff created")
        
        # Sample complaints
        sample_complaints = [
            {
                'complaint_id': 'RAIL' + str(int(datetime.now().timestamp())),
                'user_email': 'passenger@example.com',
                'pnr': '123456789',
                'complaint_text': 'The train was delayed by 2 hours',
                'category': 'Service Quality',
                'priority': 'Medium',
                'status': 'Registered',
                'created_at': datetime.now()
            }
        ]
        db.complaints.insert_many(sample_complaints)
        print("✓ Sample complaints created")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")

def load_models():
    """Load both classification models"""
    global model1, tokenizer1, config1, model2, tokenizer2, config2
    
    try:
        # Model 1: Category Classification (updated path)
        model1_path = r"models/category"
        config1_path = r"models/category/config.json"
        
        print("Loading Category Model...")
        with open(config1_path, 'r') as f:
            config1 = json.load(f)
        
        tokenizer1 = AutoTokenizer.from_pretrained(model1_path)
        model1 = AutoModelForSequenceClassification.from_pretrained(
            model1_path,
            trust_remote_code=True
        )
        # Use label mappings from the trained model config (not hardcoded)
        model1.eval()
        
        # Model 2: Priority Classification (updated path)
        model2_path = r"models/Proirity"
        config2_path = r"models/Proirity/config.json"
        
        print("Loading Priority Model...")
        with open(config2_path, 'r') as f:
            config2 = json.load(f)
        
        tokenizer2 = AutoTokenizer.from_pretrained(model2_path)
        model2 = AutoModelForSequenceClassification.from_pretrained(
            model2_path,
            trust_remote_code=True
        )
        # Use label mappings from the trained model config (not hardcoded)
        model2.eval()
        
        print("✓ Both models loaded successfully!")
        return True
    except Exception as e:
        print(f"Error loading models: {e}")
        import traceback
        traceback.print_exc()
        return False

def predict_text(text, model, tokenizer, config):
    """Make prediction on input text"""
    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=1)
        predicted_class = torch.argmax(probabilities, dim=1).item()
        
        # Resolve id2label from config or model; fall back to label2id inversion when needed
        id2label = config.get('id2label') or getattr(model.config, 'id2label', {}) or {}
        if not id2label:
            label2id = config.get('label2id') or getattr(model.config, 'label2id', {}) or {}
            id2label = {str(v): k for k, v in label2id.items()}

        predicted_label = id2label.get(str(predicted_class), f"LABEL_{predicted_class}")
        
        # DEBUG LOGGING
        print(f"[DEBUG] Predicted class: {predicted_class}")
        print(f"[DEBUG] id2label mapping: {id2label}")
        print(f"[DEBUG] Predicted label: {predicted_label}")

        # Build ordered class list for clients (by index)
        classes = [id2label[str(i)] for i in range(len(id2label)) if str(i) in id2label]
        
        scores = probabilities[0].tolist()
        
        return {
            'predicted_class': predicted_class,
            'predicted_label': predicted_label,
            'confidence': float(scores[predicted_class]),
            'all_scores': {id2label.get(str(i), f"LABEL_{i}"): float(score) for i, score in enumerate(scores)},
            'classes': classes,
            'id2label': id2label
        }
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None

# ==================== MongoDB Endpoints ====================

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register_user():
    """Register a new passenger user"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        
        if not email or not password or not name:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        if db.users.find_one({'email': email}):
            return jsonify({'error': 'Email already registered'}), 409
        
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        user = {
            'email': email,
            'password': hashed_password,
            'name': name,
            'phone': phone,
            'role': 'passenger',
            'created_at': datetime.now()
        }
        
        result = db.users.insert_one(user)
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user_id': str(result.inserted_id)
        }), 201
    except Exception as e:
        print(f"Error in /api/auth/register: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login_user():
    """Login user (passenger or staff)"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'passenger').strip()
        
        if not email or not password:
            return jsonify({'error': 'Missing email or password'}), 400
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        if role == 'staff':
            # For staff, email contains emp_id, search by emp_id
            user = db.staff.find_one({'emp_id': email, 'password': hashed_password})
            user_field = 'emp_id'
        else:
            user = db.users.find_one({'email': email, 'password': hashed_password})
            user_field = 'email'
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        response_data = {
            'success': True,
            'message': 'Login successful',
            'user': {
                'email': user.get('email'),
                'name': user.get('name'),
                'role': user.get('role', role),
                'id': str(user.get('_id'))
            }
        }
        
        # Include department for staff users
        if role == 'staff' and user.get('department'):
            response_data['user']['department'] = user.get('department')
        
        return jsonify(response_data), 200
    except Exception as e:
        print(f"Error in /api/auth/login: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/complaints/submit', methods=['POST', 'OPTIONS'])
def submit_complaint():
    """Submit a new complaint"""
    try:
        # Handle OPTIONS request for CORS
        if request.method == 'OPTIONS':
            return '', 204
            
        data = request.get_json()
        if not data:
            print("Error: No JSON data received")
            return jsonify({'error': 'No data provided'}), 400
            
        user_email = data.get('user_email', '').strip()
        pnr = data.get('pnr', '').strip()
        complaint_text = data.get('complaint_text', '').strip()
        category = data.get('category', '').strip()
        priority = data.get('priority', '').strip()
        
        print(f"Received complaint submission:")
        print(f"  - User: {user_email}")
        print(f"  - PNR: {pnr}")
        print(f"  - Category: {category}")
        print(f"  - Priority: {priority}")
        print(f"  - Text length: {len(complaint_text)}")
        
        if not user_email or not complaint_text:
            error_msg = f"Missing fields - email: {bool(user_email)}, text: {bool(complaint_text)}"
            print(f"Error: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # Generate complaint ID
        complaint_id = 'RAIL' + str(int(datetime.now().timestamp()))
        
        # Get the department for this category
        department = get_department_for_category(category)
        
        complaint = {
            'complaint_id': complaint_id,
            'user_email': user_email,
            'pnr': pnr,
            'complaint_text': complaint_text,
            'category': category,
            'priority': priority,
            'status': 'Registered',
            'department': department,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'resolution': None
        }
        
        result = db.complaints.insert_one(complaint)
        print(f"✓ Complaint {complaint_id} saved to MongoDB")
        
        # Create notification for the respective department
        create_notification(complaint_id, category, priority, user_email, complaint_text)
        
        return jsonify({
            'success': True,
            'message': 'Complaint submitted successfully',
            'complaint_id': complaint_id,
            'status': 'Registered',
            'department': get_department_for_category(category)
        }), 201
    except Exception as e:
        print(f"Error in /api/complaints/submit: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/complaints/all', methods=['GET'])
def get_all_complaints():
    """Get all complaints with optional filtering"""
    try:
        user_email = request.args.get('user_email', '').strip()
        status = request.args.get('status', '').strip()
        
        print(f"\n=== GET /api/complaints/all ===")
        print(f"user_email: {user_email}")
        print(f"status: {status}")
        
        query = {}
        if user_email:
            query['user_email'] = user_email
        if status:
            query['status'] = status
        
        print(f"Query: {query}")
        complaints = list(db.complaints.find(query).sort('created_at', -1))
        print(f"Found {len(complaints)} complaints")
        
        # Convert to JSON-serializable format
        result_complaints = []
        for idx, complaint in enumerate(complaints):
            try:
                print(f"\nProcessing complaint {idx}:")
                print(f"  Keys: {list(complaint.keys())}")
                
                # Debug each field
                created_at_val = complaint.get('created_at', '')
                print(f"  created_at type: {type(created_at_val)}, value: {created_at_val}")
                
                updated_at_val = complaint.get('updated_at', '')
                print(f"  updated_at type: {type(updated_at_val)}, value: {updated_at_val}")
                
                c = {
                    '_id': str(complaint.get('_id', '')),
                    'complaint_id': complaint.get('complaint_id', ''),
                    'user_email': complaint.get('user_email', ''),
                    'category': complaint.get('category', 'N/A'),
                    'priority': complaint.get('priority', 'N/A'),
                    'status': complaint.get('status', 'Registered'),
                    'created_at': str(created_at_val),
                    'updated_at': str(updated_at_val),
                    'pnr': complaint.get('pnr', ''),
                    'complaint_text': complaint.get('complaint_text', ''),
                    'resolution': complaint.get('resolution')
                }
                print(f"  Successfully built complaint object")
                result_complaints.append(c)
            except Exception as e:
                print(f"Error processing complaint {idx}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\nBuilding response with {len(result_complaints)} complaints")
        response_obj = {
            'success': True,
            'count': len(result_complaints),
            'complaints': result_complaints
        }
        print(f"Response object built successfully")
        print(f"Calling jsonify...")
        
        result = jsonify(response_obj)
        print(f"jsonify returned successfully")
        return result, 200
    except Exception as e:
        print(f"Error in /api/complaints/all: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-user-complaints', methods=['POST'])
def fetch_user_complaints():
    """Direct database fetch for user complaints"""
    try:
        data = request.get_json()
        user_email = data.get('email', '').strip()
        
        print(f"\n=== Fetching Complaints Direct from DB ===")
        print(f"User Email: {user_email}")
        print(f"Email type: {type(user_email)}")
        print(f"Email length: {len(user_email)}")
        
        if not user_email:
            return jsonify({
                'success': False,
                'message': 'Email required',
                'complaints': []
            }), 400
        
        # Direct database query
        print(f"Querying database for: {{'user_email': '{user_email}'}}")
        complaints = list(db.complaints.find({'user_email': user_email}).sort('created_at', -1))
        
        print(f"Found {len(complaints)} complaints")
        
        # Convert to JSON-serializable format
        result_complaints = []
        for complaint in complaints:
            created_at_val = complaint.get('created_at')
            updated_at_val = complaint.get('updated_at')
            c = {
                '_id': str(complaint.get('_id', '')),
                'complaint_id': complaint.get('complaint_id', ''),
                'user_email': complaint.get('user_email', ''),
                'pnr': complaint.get('pnr', ''),
                'complaint_text': complaint.get('complaint_text', ''),
                'category': complaint.get('category', 'N/A'),
                'priority': complaint.get('priority', 'N/A'),
                'status': complaint.get('status', 'Registered'),
                'resolution': complaint.get('resolution'),
                'created_at': created_at_val.isoformat() if hasattr(created_at_val, 'isoformat') else str(created_at_val) if created_at_val else '',
                'updated_at': updated_at_val.isoformat() if hasattr(updated_at_val, 'isoformat') else str(updated_at_val) if updated_at_val else ''
            }
            result_complaints.append(c)
            print(f"  - {c['complaint_id']}: {c['category']} ({c['status']})")
        
        return jsonify({
            'success': True,
            'count': len(result_complaints),
            'complaints': result_complaints,
            'message': f'Found {len(result_complaints)} complaints'
        }), 200
        
    except Exception as e:
        print(f"\n!!! Error in /api/get-user-complaints: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e),
            'complaints': []
        }), 500

@app.route('/api/complaints/user/<user_email>', methods=['GET'])
def get_user_complaints(user_email):
    """Get all complaints for a specific user by email"""
    try:
        print(f"Fetching complaints for user: {user_email}")
        
        # URL decode the email
        import urllib.parse
        user_email = urllib.parse.unquote(user_email).strip()
        
        print(f"Decoded email: {user_email}")
        
        complaints = list(db.complaints.find({'user_email': user_email}).sort('created_at', -1))
        
        print(f"Found {len(complaints)} complaints")
        
        # Convert ObjectId to string for JSON serialization - just use str() for all dates
        for complaint in complaints:
            complaint['_id'] = str(complaint['_id'])
            # Simply convert dates to strings without trying isoformat
            if complaint.get('created_at'):
                complaint['created_at'] = str(complaint['created_at'])
            else:
                complaint['created_at'] = ''
            if complaint.get('updated_at'):
                complaint['updated_at'] = str(complaint['updated_at'])
            else:
                complaint['updated_at'] = ''
        
        return jsonify({
            'success': True,
            'count': len(complaints),
            'complaints': complaints
        }), 200
    except Exception as e:
        print(f"Error in /api/complaints/user/<email>: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/get-user-theft-reports', methods=['POST'])
def fetch_user_theft_reports():
    """Direct database fetch for user theft/lost reports"""
    try:
        data = request.get_json()
        user_email = data.get('email', '').strip()
        
        print(f"\n=== Fetching Theft/Lost Reports Direct from DB ===")
        print(f"User Email: {user_email}")
        
        if not user_email:
            return jsonify({
                'success': False,
                'message': 'Email required',
                'reports': []
            }), 400
        
        # Direct database query
        print(f"Querying database for: {{'email': '{user_email}'}}")
        reports = list(db.theft_lost_reports.find({'email': user_email}).sort('created_at', -1))
        
        print(f"Found {len(reports)} theft/lost reports")
        
        # Convert to JSON-serializable format
        result_reports = []
        for report in reports:
            created_at_val = report.get('created_at')
            r = {
                '_id': str(report.get('_id', '')),
                'report_id': report.get('report_id', ''),
                'email': report.get('email', ''),
                'itemType': report.get('itemType', ''),
                'itemDescription': report.get('itemDescription', ''),
                'estimatedValue': report.get('estimatedValue', '0'),
                'color': report.get('color', ''),
                'serialNumber': report.get('serialNumber', ''),
                'incidentDate': report.get('incidentDate', ''),
                'incidentTime': report.get('incidentTime', ''),
                'platformNumber': report.get('platformNumber', ''),
                'trainNumber': report.get('trainNumber', ''),
                'trainName': report.get('trainName', ''),
                'boarding': report.get('boarding', ''),
                'destination': report.get('destination', ''),
                'status': report.get('status', 'Registered'),
                'resolution': report.get('resolution'),
                'created_at': created_at_val.isoformat() if hasattr(created_at_val, 'isoformat') else str(created_at_val) if created_at_val else ''
            }
            result_reports.append(r)
            print(f"  - {r['report_id']}: {r['itemType']} ({r['status']})")
        
        return jsonify({
            'success': True,
            'count': len(result_reports),
            'reports': result_reports,
            'message': f'Found {len(result_reports)} reports'
        }), 200
        
    except Exception as e:
        print(f"\n!!! Error in /api/get-user-theft-reports: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e),
            'reports': []
        }), 500

@app.route('/api/complaints/<complaint_id>', methods=['GET'])
def get_complaint(complaint_id):
    """Get a specific complaint by ID"""
    try:
        complaint = db.complaints.find_one({'complaint_id': complaint_id})
        
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        complaint['_id'] = str(complaint['_id'])
        # Simply convert dates to strings
        if complaint.get('created_at'):
            complaint['created_at'] = str(complaint['created_at'])
        else:
            complaint['created_at'] = ''
        if complaint.get('updated_at'):
            complaint['updated_at'] = str(complaint['updated_at'])
        else:
            complaint['updated_at'] = ''
        
        return jsonify({
            'success': True,
            'complaint': complaint
        }), 200
    except Exception as e:
        print(f"Error in /api/complaints/<id>: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/complaints/<complaint_id>/update', methods=['PUT'])
def update_complaint(complaint_id):
    """Update complaint status or resolution"""
    try:
        data = request.get_json()
        status = data.get('status')
        resolution = data.get('resolution')
        
        update_data = {'updated_at': datetime.now()}
        if status:
            update_data['status'] = status
        if resolution:
            update_data['resolution'] = resolution
        
        result = db.complaints.update_one(
            {'complaint_id': complaint_id},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Complaint not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Complaint updated successfully'
        }), 200
    except Exception as e:
        print(f"Error in /api/complaints/<id>/update: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/complaints/category/<category>', methods=['GET'])
def get_complaints_by_category(category):
    """Get all complaints for a specific category"""
    try:
        print(f"\n=== GET /api/complaints/category/{category} ===")
        
        # URL decode the category
        import urllib.parse
        category = urllib.parse.unquote(category).strip()
        
        print(f"Fetching complaints for category: {category}")
        
        # Query database for complaints with the specified category
        complaints = list(db.complaints.find({'category': category}).sort('created_at', -1))
        
        print(f"Found {len(complaints)} complaints for category '{category}'")
        
        # Convert to JSON-serializable format
        result_complaints = []
        for complaint in complaints:
            created_at_val = complaint.get('created_at')
            updated_at_val = complaint.get('updated_at')
            c = {
                '_id': str(complaint.get('_id', '')),
                'complaint_id': complaint.get('complaint_id', ''),
                'user_email': complaint.get('user_email', ''),
                'pnr': complaint.get('pnr', ''),
                'complaint_text': complaint.get('complaint_text', ''),
                'category': complaint.get('category', 'N/A'),
                'priority': complaint.get('priority', 'N/A'),
                'status': complaint.get('status', 'Registered'),
                'resolution': complaint.get('resolution'),
                'created_at': created_at_val.isoformat() if hasattr(created_at_val, 'isoformat') else str(created_at_val) if created_at_val else '',
                'updated_at': updated_at_val.isoformat() if hasattr(updated_at_val, 'isoformat') else str(updated_at_val) if updated_at_val else ''
            }
            result_complaints.append(c)
            print(f"  - {c['complaint_id']}: {c['status']}")
        
        return jsonify({
            'success': True,
            'category': category,
            'count': len(result_complaints),
            'complaints': result_complaints,
            'message': f'Found {len(result_complaints)} complaints in category "{category}"'
        }), 200
        
    except Exception as e:
        print(f"\n!!! Error in /api/complaints/category/<category>: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e),
            'complaints': []
        }), 500

# ===== NOTIFICATION ENDPOINTS =====

@app.route('/api/notifications/department/<path:department>', methods=['GET'])
def get_department_notifications(department):
    """Get all notifications for a specific department"""
    try:
        import urllib.parse
        department = urllib.parse.unquote(department).strip()
        
        print(f"\n=== GET /api/notifications/department/{department} ===")
        
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        show_read = request.args.get('show_read', 'false').lower() == 'true'
        
        # Build query
        query = {'department': department}
        if not show_read:
            query['is_read'] = False
        
        notifications = list(db.notifications.find(query).sort('created_at', -1).limit(limit))
        
        # Convert to JSON-serializable format
        result_notifications = []
        for notif in notifications:
            created_at_val = notif.get('created_at')
            n = {
                '_id': str(notif.get('_id', '')),
                'complaint_id': notif.get('complaint_id', ''),
                'department': notif.get('department', ''),
                'category': notif.get('category', ''),
                'priority': notif.get('priority', ''),
                'user_email': notif.get('user_email', ''),
                'complaint_text': notif.get('complaint_text', ''),
                'is_read': notif.get('is_read', False),
                'created_at': created_at_val.isoformat() if hasattr(created_at_val, 'isoformat') else str(created_at_val)
            }
            result_notifications.append(n)
        
        print(f"Found {len(result_notifications)} notifications for {department}")
        
        return jsonify({
            'success': True,
            'department': department,
            'count': len(result_notifications),
            'notifications': result_notifications
        }), 200
        
    except Exception as e:
        print(f"Error in /api/notifications/department/<department>: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/unread-count', methods=['GET'])
def get_unread_notification_count():
    """Get unread notification count by department"""
    try:
        department = request.args.get('department', '').strip()
        
        print(f"\n=== GET /api/notifications/unread-count ===")
        print(f"Department: {department}")
        
        query = {'is_read': False}
        if department:
            query['department'] = department
        
        unread_count = db.notifications.count_documents(query)
        
        print(f"Unread count: {unread_count}")
        
        return jsonify({
            'success': True,
            'unread_count': unread_count,
            'department': department
        }), 200
        
    except Exception as e:
        print(f"Error in /api/notifications/unread-count: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<notification_id>/read', methods=['PUT', 'OPTIONS'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        if request.method == 'OPTIONS':
            return '', 204
        
        print(f"\n=== PUT /api/notifications/{notification_id}/read ===")
        
        result = db.notifications.update_one(
            {'_id': ObjectId(notification_id)},
            {'$set': {'is_read': True, 'updated_at': datetime.now()}}
        )
        
        if result.modified_count > 0:
            print(f"✓ Notification {notification_id} marked as read")
            return jsonify({
                'success': True,
                'message': 'Notification marked as read'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Notification not found'
            }), 404
            
    except Exception as e:
        print(f"Error in /api/notifications/<notification_id>/read: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/mark-all-read', methods=['PUT', 'OPTIONS'])
def mark_all_notifications_read():
    """Mark all notifications as read for a department"""
    try:
        if request.method == 'OPTIONS':
            return '', 204
        
        data = request.get_json() or {}
        department = data.get('department', '').strip()
        
        print(f"\n=== PUT /api/notifications/mark-all-read ===")
        print(f"Department: {department}")
        
        query = {'is_read': False}
        if department:
            query['department'] = department
        
        result = db.notifications.update_many(
            query,
            {'$set': {'is_read': True, 'updated_at': datetime.now()}}
        )
        
        print(f"✓ Marked {result.modified_count} notifications as read")
        
        return jsonify({
            'success': True,
            'modified_count': result.modified_count,
            'message': f'Marked {result.modified_count} notifications as read'
        }), 200
        
    except Exception as e:
        print(f"Error in /api/notifications/mark-all-read: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<notification_id>', methods=['DELETE', 'OPTIONS'])
def delete_notification(notification_id):
    """Delete a notification"""
    try:
        if request.method == 'OPTIONS':
            return '', 204
        
        print(f"\n=== DELETE /api/notifications/{notification_id} ===")
        
        result = db.notifications.delete_one({'_id': ObjectId(notification_id)})
        
        if result.deleted_count > 0:
            print(f"✓ Notification {notification_id} deleted")
            return jsonify({
                'success': True,
                'message': 'Notification deleted'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Notification not found'
            }), 404
            
    except Exception as e:
        print(f"Error in /api/notifications/<notification_id>: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== Complaint Status Management ====================

@app.route('/api/complaints/<complaint_id>/status', methods=['PUT', 'OPTIONS'])
def update_complaint_status(complaint_id):
    """Update complaint status (for staff members)"""
    try:
        if request.method == 'OPTIONS':
            return '', 204
        
        data = request.get_json()
        new_status = data.get('status', '').strip()
        resolution = data.get('resolution', '').strip()
        
        print(f"\n=== UPDATE /api/complaints/{complaint_id}/status ===")
        print(f"New Status: {new_status}")
        print(f"Resolution: {resolution}")
        
        # Valid status values
        valid_statuses = ['Registered', 'Processing', 'Completed']
        
        if not new_status or new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Update complaint
        update_data = {
            'status': new_status,
            'updated_at': datetime.now()
        }
        
        if resolution:
            update_data['resolution'] = resolution
        
        result = db.complaints.update_one(
            {'complaint_id': complaint_id},
            {'$set': update_data}
        )
        
        if result.matched_count > 0:
            print(f"✓ Complaint {complaint_id} status updated to: {new_status}")
            
            # Also mark notification as read if completed
            if new_status in ['Completed']:
                db.notifications.update_many(
                    {'complaint_id': complaint_id, 'is_read': False},
                    {'$set': {'is_read': True, 'updated_at': datetime.now()}}
                )
            
            return jsonify({
                'success': True,
                'message': f'Complaint status updated to {new_status}',
                'complaint_id': complaint_id,
                'status': new_status
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
            
    except Exception as e:
        print(f"Error in /api/complaints/<complaint_id>/status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/complaints/<complaint_id>/feedback', methods=['POST', 'OPTIONS'])
def submit_complaint_feedback(complaint_id):
    """Submit feedback and rating for a complaint"""
    try:
        if request.method == 'OPTIONS':
            return '', 200
        
        data = request.get_json()
        rating = data.get('rating')
        feedback = data.get('feedback', '')
        
        print(f"\n=== POST /api/complaints/{complaint_id}/feedback ===")
        print(f"Rating: {rating}")
        print(f"Feedback: {feedback[:100]}...")
        
        # Validate rating
        if not rating or rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'message': 'Invalid rating. Must be between 1 and 5.'
            }), 400
        
        # Update complaint with feedback
        feedback_data = {
            'rating': rating,
            'feedback': feedback,
            'feedback_submitted_at': datetime.now()
        }
        
        result = db.complaints.update_one(
            {'complaint_id': complaint_id},
            {'$set': {'feedback': feedback_data}}
        )
        
        if result.matched_count > 0:
            print(f"✓ Feedback submitted for complaint {complaint_id}")
            return jsonify({
                'success': True,
                'message': 'Thank you for your feedback!',
                'complaint_id': complaint_id
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
            
    except Exception as e:
        print(f"Error in /api/complaints/<complaint_id>/feedback: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/complaints/department/<path:department>', methods=['GET'])
def get_department_complaints(department):
    """Get all complaints for a specific department (for staff view)"""
    try:
        import urllib.parse
        department = urllib.parse.unquote(department).strip()
        
        print(f"\n=== GET /api/complaints/department/{department} ===")
        
        complaints = list(db.complaints.find({'department': department}).sort('created_at', -1))
        
        print(f"Found {len(complaints)} complaints for {department}")
        
        # Convert to JSON-serializable format
        result_complaints = []
        for complaint in complaints:
            c = {
                '_id': str(complaint.get('_id', '')),
                'complaint_id': complaint.get('complaint_id', ''),
                'user_email': complaint.get('user_email', ''),
                'pnr': complaint.get('pnr', ''),
                'complaint_text': complaint.get('complaint_text', ''),
                'category': complaint.get('category', ''),
                'priority': complaint.get('priority', ''),
                'status': complaint.get('status', 'Registered'),
                'resolution': complaint.get('resolution'),
                'created_at': str(complaint.get('created_at', '')) if complaint.get('created_at') else '',
                'updated_at': str(complaint.get('updated_at', '')) if complaint.get('updated_at') else '',
                'department': complaint.get('department', '')
            }
            
            # Include feedback if it exists
            feedback = complaint.get('feedback')
            if feedback:
                c['feedback'] = {
                    'rating': feedback.get('rating'),
                    'feedback': feedback.get('feedback', ''),
                    'feedback_submitted_at': str(feedback.get('feedback_submitted_at', '')) if feedback.get('feedback_submitted_at') else ''
                }
            
            result_complaints.append(c)
        
        return jsonify({
            'success': True,
            'count': len(result_complaints),
            'complaints': result_complaints
        }), 200
        
    except Exception as e:
        print(f"Error in /api/complaints/department/{department}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        total_complaints = db.complaints.count_documents({})
        total_users = db.users.count_documents({})
        
        status_breakdown = list(db.complaints.aggregate([
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]))
        
        return jsonify({
            'success': True,
            'stats': {
                'total_complaints': total_complaints,
                'total_users': total_users,
                'status_breakdown': status_breakdown
            }
        }), 200
    except Exception as e:
        print(f"Error in /api/stats: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== Theft/Lost Items Endpoints ====================

@app.route('/api/theft-lost', methods=['POST', 'OPTIONS'])
def submit_theft_lost_report():
    """Submit a theft/lost item report"""
    try:
        if request.method == 'OPTIONS':
            return '', 204
        
        data = request.json
        
        # Validate required fields
        required_fields = ['fullName', 'email', 'phone', 'pnr', 'itemType', 'itemDescription']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Generate unique report ID
        report_id = 'THEFT' + str(uuid.uuid4())[:8].upper()
        
        # Create report document
        report = {
            'report_id': report_id,
            'fullName': data.get('fullName'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'pnr': data.get('pnr'),
            'itemType': data.get('itemType'),
            'itemDescription': data.get('itemDescription'),
            'estimatedValue': data.get('estimatedValue'),
            'color': data.get('color'),
            'serialNumber': data.get('serialNumber'),
            'incidentDate': data.get('incidentDate'),
            'incidentTime': data.get('incidentTime'),
            'platformNumber': data.get('platformNumber'),
            'trainNumber': data.get('trainNumber'),
            'trainName': data.get('trainName'),
            'boarding': data.get('boarding'),
            'destination': data.get('destination'),
            'status': 'Registered',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Insert into database
        result = db.theft_lost_reports.insert_one(report)
        
        # Create notification for Lost/Theft department
        create_theft_lost_notification(
            report_id,
            data.get('itemType'),
            data.get('itemDescription'),
            data.get('email'),
            data.get('fullName')
        )
        
        print(f"✓ Theft/Lost report submitted: {report_id}")
        
        return jsonify({
            'success': True,
            'message': 'Report submitted successfully',
            'report_id': report_id
        }), 201
        
    except Exception as e:
        print(f"Error submitting theft/lost report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/theft-lost/<report_id>', methods=['GET'])
def get_theft_lost_report(report_id):
    """Get a specific theft/lost report"""
    try:
        report = db.theft_lost_reports.find_one({'report_id': report_id})
        
        if not report:
            return jsonify({'success': False, 'error': 'Report not found'}), 404
        
        report['_id'] = str(report['_id'])
        
        return jsonify({
            'success': True,
            'report': report
        }), 200
        
    except Exception as e:
        print(f"Error fetching theft/lost report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/theft-lost/email/<email>', methods=['GET'])
def get_theft_lost_by_email(email):
    """Get all theft/lost reports by email"""
    try:
        import urllib.parse
        email = urllib.parse.unquote(email).strip()
        
        reports = list(db.theft_lost_reports.find({'email': email}).sort('created_at', -1))
        
        for report in reports:
            report['_id'] = str(report['_id'])
            if 'created_at' in report:
                report['created_at'] = report['created_at'].isoformat()
            if 'updated_at' in report:
                report['updated_at'] = report['updated_at'].isoformat()
        
        return jsonify({
            'success': True,
            'reports': reports,
            'count': len(reports)
        }), 200
        
    except Exception as e:
        print(f"Error fetching theft/lost reports: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/theft-lost/all', methods=['GET'])
def get_all_theft_lost_reports():
    """Get all theft/lost reports for Lost/Theft department staff"""
    try:
        reports = list(db.theft_lost_reports.find().sort('created_at', -1).limit(100))
        
        # Convert ObjectId to string and format for display
        result_reports = []
        for report in reports:
            r = {
                '_id': str(report.get('_id', '')),
                'report_id': report.get('report_id', ''),
                'complaint_id': report.get('report_id', ''),  # For compatibility
                'user_email': report.get('email', ''),
                'fullName': report.get('fullName', ''),
                'pnr': report.get('pnr', ''),
                'itemType': report.get('itemType', ''),
                'itemDescription': report.get('itemDescription', ''),
                'category': 'Lost/Theft',
                'created_at': report.get('created_at', ''),
                'status': report.get('status', 'Registered'),
                'phone': report.get('phone', ''),
                'trainNumber': report.get('trainNumber', ''),
                'platformNumber': report.get('platformNumber', ''),
                'boarding': report.get('boarding', ''),
                'destination': report.get('destination', ''),
                'estimatedValue': report.get('estimatedValue', ''),
                'color': report.get('color', '')
            }
            result_reports.append(r)
        
        print(f"Found {len(result_reports)} theft/lost reports")
        
        return jsonify({
            'success': True,
            'reports': result_reports,
            'count': len(result_reports)
        }), 200
        
    except Exception as e:
        print(f"Error fetching all theft/lost reports: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/theft-lost/<report_id>/status', methods=['PUT'])
def update_theft_lost_status(report_id):
    """Update the status of a theft/lost report"""
    try:
        data = request.json
        
        new_status = data.get('status')
        resolution = data.get('resolution', '')
        
        if not new_status:
            return jsonify({'success': False, 'message': 'Status is required'}), 400
        
        # Update the report
        result = db.theft_lost_reports.update_one(
            {'report_id': report_id},
            {
                '$set': {
                    'status': new_status,
                    'resolution': resolution,
                    'updated_at': datetime.now()
                }
            }
        )
        
        if result.matched_count == 0:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        print(f"✓ Theft/Lost report {report_id} status updated to: {new_status}")
        
        return jsonify({
            'success': True,
            'message': 'Report status updated successfully',
            'report_id': report_id,
            'status': new_status
        }), 200
        
    except Exception as e:
        print(f"Error updating theft/lost report status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== Complaint Classification Endpoint ====================

@app.route('/api/classify', methods=['POST'])
def classify_complaint():
    """
    Classify a complaint by category and priority
    Request body: {
        "pnr": "string",
        "complaint": "string"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'complaint' not in data:
            return jsonify({'error': 'Missing complaint text'}), 400
        
        complaint_text = data.get('complaint', '').strip()
        pnr = data.get('pnr', '').strip()
        
        if not complaint_text:
            return jsonify({'error': 'Complaint text cannot be empty'}), 400
        
        # Get category prediction
        category_result = predict_text(complaint_text, model1, tokenizer1, config1)
        if category_result is None:
            return jsonify({'error': 'Error classifying complaint'}), 500
        
        # Get priority prediction
        priority_result = predict_text(complaint_text, model2, tokenizer2, config2)
        if priority_result is None:
            return jsonify({'error': 'Error determining priority'}), 500
        
        # Prepare response
        response = {
            'success': True,
            'pnr': pnr,
            'complaint_text': complaint_text[:100] + ('...' if len(complaint_text) > 100 else ''),
            'category': {
                'predicted': category_result['predicted_label'],
                'confidence': category_result['confidence'],
                'all_scores': category_result['all_scores'],
                'classes': category_result.get('classes', []),
                'id2label': category_result.get('id2label', {})
            },
            'priority': {
                'predicted': priority_result['predicted_label'],
                'confidence': priority_result['confidence'],
                'all_scores': priority_result['all_scores'],
                'classes': priority_result.get('classes', []),
                'id2label': priority_result.get('id2label', {})
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        print(f"Error in /api/classify: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    models_loaded = model1 is not None and model2 is not None
    return jsonify({
        'status': 'healthy' if models_loaded else 'models not loaded',
        'models_loaded': models_loaded,
        'timestamp': datetime.now().isoformat()
    }), 200 if models_loaded else 503

@app.route('/api/test-db', methods=['GET'])
def test_db():
    """Test database and models connectivity"""
    try:
        # Test MongoDB connection
        mongodb_status = False
        try:
            db.command('ping')
            mongodb_status = True
        except:
            pass
        
        # Test models
        models_status = model1 is not None and model2 is not None
        
        return jsonify({
            'success': True,
            'mongodb_status': mongodb_status,
            'models_status': models_status,
            'api_status': True
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'mongodb_status': False,
            'models_status': False,
            'api_status': False
        }), 500

@app.route('/api/db-status', methods=['GET'])
def db_status():
    """Database connection health check"""
    try:
        # Test MongoDB connection
        if db is None:
            return jsonify({
                'status': 'disconnected',
                'database_connection': False,
                'connection_health': 'No database connection',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        try:
            db.command('ping')
            return jsonify({
                'status': 'connected',
                'database_connection': True,
                'connection_health': 'Database connection healthy',
                'timestamp': datetime.now().isoformat()
            }), 200
        except Exception as e:
            return jsonify({
                'status': 'error',
                'database_connection': False,
                'connection_health': f'Connection error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'database_connection': False,
            'connection_health': f'Unexpected error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def serve_index():
    """Serve index.html at root"""
    return app.send_static_file('index.html')

@app.route('/api/', methods=['GET'])
def api_info():
    return jsonify({
        'service': 'Railway Complaint Classification API',
        'version': '1.0',
        'endpoints': {
            'POST /api/classify': 'Classify complaint by category and priority',
            'GET /api/health': 'Health check',
            'POST /api/chat': 'Chat with AI assistant'
        }
    }), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chatbot requests"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        language = data.get('language', 'en')
        
        if not user_message:
            return jsonify({
                'success': False,
                'response': 'Please provide a message.'
            }), 400
        
        # Simple rule-based chatbot responses
        response = generate_chatbot_response(user_message, language)
        
        return jsonify({
            'success': True,
            'response': response
        }), 200
        
    except Exception as e:
        print(f"Chatbot Error: {e}")
        return jsonify({
            'success': False,
            'response': 'Sorry, I encountered an error. Please try again.'
        }), 500

def generate_chatbot_response(user_message, language='en'):
    """Generate chatbot response based on user input"""
    message_lower = user_message.lower()
    
    # Dictionary of responses by language
    responses = {
        'en': {
            'track': "You can track your complaint using the 'Track Complaint' page. Just enter your complaint ID to see the current status and updates.",
            'register': "To register a new complaint, click on 'Register New Complaint' and fill in the details about your complaint.",
            'lost': "You can report lost or stolen items using the 'Report Lost/Stolen' section. Provide details about the item and your journey.",
            'help': "I can help you with:\n1. Tracking complaints\n2. Registering new complaints\n3. Reporting lost items\n4. General questions about the system",
            'hello': "Hello! Welcome to Railway Complaint System. How can I assist you today?",
            'thank': "You're welcome! Is there anything else I can help you with?",
            'default': "I can help you with complaint tracking, registration, and reporting lost items. What would you like to do?"
        },
        'ta': {
            'track': "நீங்கள் 'புகாரை கண்காணி' பக்கத்தைப் பயன்படுத்தி உங்கள் புகாரைக் கண்காணிக்கலாம். உங்கள் புகார் ID ஐ உள்ளிட்டு தற்போதைய நிலை மற்றும் புதுப்பிப்புகளைப் பார்க்கவும்.",
            'register': "புதிய புகாரைப் பதிவுசெய்ய, 'புதிய புகாரைப் பதிவுசெய்' என்பதைக் கிளிக் செய்து உங்கள் புகாரின் விவரங்களை நிரப்பவும்.",
            'lost': "இழந்த அல்லது திருடப்பட்ட பொருட்களைப் புகாரளிக்க 'இழந்த/திருடப்பட்ட பொருள்களைப் புகாரளி' பிரிவைப் பயன்படுத்தவும்.",
            'hello': "வணக்கம்! இரயில்வே புகாரளிக்கும் அமைப்பில் நல்வரவு. இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?",
            'help': "நான் உதவ முடியும்:\n1. புகாரைக் கண்காணிக்க\n2. புதிய புகாரைப் பதிவுசெய்ய\n3. இழந்த பொருட்களைப் புகாரளிக்க\n4. கணினி பற்றிய சாதாரண கேள்விகளுக்கு",
            'default': "நான் புகாரைக் கண்காணிக்க, பதிவுசெய்ய மற்றும் இழந்த பொருட்களைப் புகாரளிக்க உதவ முடியும். நீங்கள் என்ன செய்ய விரும்புகிறீர்கள்?"
        },
        'hi': {
            'track': "आप 'शिकायत ट्रैक करें' पृष्ठ का उपयोग करके अपनी शिकायत को ट्रैक कर सकते हैं। अपनी शिकायत ID दर्ज करें और वर्तमान स्थिति देखें।",
            'register': "एक नई शिकायत दर्ज करने के लिए, 'नई शिकायत दर्ज करें' पर क्लिक करें और अपनी शिकायत का विवरण भरें।",
            'lost': "खोई हुई या चोरी हुई वस्तुओं की रिपोर्ट करने के लिए 'खोई हुई/चोरी हुई रिपोर्ट करें' अनुभाग का उपयोग करें।",
            'hello': "नमस्ते! रेलवे शिकायत प्रणाली में आपका स्वागत है। मैं आपकी कैसे सहायता कर सकता हूँ?",
            'help': "मैं आपकी मदद कर सकता हूँ:\n1. शिकायत ट्रैक करने में\n2. नई शिकायत दर्ज करने में\n3. खोई हुई वस्तुओं की रिपोर्ट करने में\n4. सामान्य प्रश्नों का उत्तर देने में",
            'default': "मैं शिकायत ट्रैकिंग, पंजीकरण और खोई हुई वस्तुओं की रिपोर्टिंग में मदद कर सकता हूँ। आप क्या करना चाहते हैं?"
        }
    }
    
    # Get response dictionary for the language
    lang_responses = responses.get(language, responses['en'])
    
    # Check for keywords in user message
    if any(word in message_lower for word in ['track', 'status', 'check', 'complaint id']):
        return lang_responses.get('track', lang_responses['default'])
    elif any(word in message_lower for word in ['register', 'file', 'new', 'complaint']):
        return lang_responses.get('register', lang_responses['default'])
    elif any(word in message_lower for word in ['lost', 'stolen', 'missing', 'theft']):
        return lang_responses.get('lost', lang_responses['default'])
    elif any(word in message_lower for word in ['help', 'can you', 'what']):
        return lang_responses.get('help', lang_responses['default'])
    elif any(word in message_lower for word in ['hi', 'hello', 'hey']):
        return lang_responses.get('hello', lang_responses['default'])
    elif any(word in message_lower for word in ['thanks', 'thank', 'thankyou']):
        return lang_responses.get('thank', lang_responses['default'])
    else:
        return lang_responses.get('default', lang_responses['default'])

# User Profile Endpoints
@app.route('/api/users/<email>', methods=['GET'])
def get_user_profile(email):
    """Get user profile by email"""
    try:
        user = db.users.find_one({'email': email})
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Remove sensitive data
        user.pop('password', None)
        user['_id'] = str(user['_id'])
        
        return jsonify({'success': True, 'user': user}), 200
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/<email>', methods=['PUT'])
def update_user_profile(email):
    """Update user profile"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Find user
        user = db.users.find_one({'email': email})
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Update fields (excluding email which is immutable)
        update_fields = {}
        allowed_fields = ['first_name', 'last_name', 'phone', 'address', 'city', 'state', 'pincode']
        
        for field in allowed_fields:
            if field in data:
                update_fields[field] = data[field]
        
        if not update_fields:
            return jsonify({'success': False, 'message': 'No valid fields to update'}), 400
        
        # Update in database
        result = db.users.update_one(
            {'email': email},
            {'$set': update_fields}
        )
        
        if result.modified_count > 0:
            # Fetch updated user
            updated_user = db.users.find_one({'email': email})
            updated_user.pop('password', None)
            updated_user['_id'] = str(updated_user['_id'])
            
            return jsonify({'success': True, 'message': 'Profile updated successfully', 'user': updated_user}), 200
        else:
            return jsonify({'success': False, 'message': 'No changes made'}), 200
    
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== Train Tracking Endpoint ====================
@app.route('/api/track-train/<train_number>', methods=['GET'])
def track_train(train_number):
    """Track train using RailRadar API"""
    try:
        import os
        import requests
        from datetime import datetime
        
        # Get today's date in required format (DDMMYYYY)
        journey_date = datetime.now().strftime('%d%m%Y')
        
        # RapidAPI key/host for train schedule (IRCTC). Must be provided via env.
        rapid_key = os.getenv('RAPIDAPI_KEY')
        schedule_host = 'irctc1.p.rapidapi.com'

        # RapidAPI key/host for live status (Indian Railway IRCTC). Must be provided via env.
        live_key = os.getenv('RAPIDAPI_LIVE_KEY')
        live_host = 'indian-railway-irctc.p.rapidapi.com'

        if not rapid_key or not live_key:
            return jsonify({
                'success': False,
                'message': 'Missing RapidAPI keys. Set RAPIDAPI_KEY and RAPIDAPI_LIVE_KEY environment variables.'
            }), 500

        # API endpoints
        schedule_url = f'https://{schedule_host}/api/v1/getTrainSchedule'
        schedule_params = {
            'trainNo': train_number
        }
        status_url = f'https://{live_host}/api/trains/v1/train/status'
        status_params = {
            'train_number': train_number,
            'departure_date': datetime.now().strftime('%Y%m%d'),
            'isH5': 'true',
            # These params are required by the RapidAPI endpoint per docs/playground
            'client': 'web',
            'deviceIdentifier': 'Mozilla Firefox-138.0.0.0'
        }
        
        schedule_headers = {
            'X-RapidAPI-Key': rapid_key,
            'X-RapidAPI-Host': schedule_host
        }
        status_headers = {
            'X-RapidAPI-Key': live_key,
            'X-RapidAPI-Host': live_host
        }
        
        schedule_data = None
        status_data = None
        
        # Step 1: Get Train Schedule (for route/stations)
        try:
            print(f"[SCHEDULE] Calling: {schedule_url}")
            response = requests.get(schedule_url, headers=schedule_headers, params=schedule_params, timeout=15)
            print(f"[SCHEDULE] Status: {response.status_code}")
            
            if response.status_code == 200:
                schedule_data = response.json()
                print(f"[SCHEDULE] Success! Got data")
            else:
                print(f"[SCHEDULE] Failed with status {response.status_code}")
                print(f"[SCHEDULE] Response: {response.text}")
        except Exception as e:
            print(f"[SCHEDULE] Error: {e}")
        
        # Step 2: Get Live Train Status
        try:
            print(f"[STATUS] Calling: {status_url}")
            response = requests.get(status_url, headers=status_headers, params=status_params, timeout=15)
            print(f"[STATUS] Status: {response.status_code}")
            
            if response.status_code == 200:
                status_data = response.json()
                print(f"[STATUS] Success! Got data")
            else:
                print(f"[STATUS] Failed with status {response.status_code}")
                print(f"[STATUS] Response: {response.text}")
        except Exception as e:
            print(f"[STATUS] Error: {e}")
        
        # Combine responses
        if schedule_data or status_data:
            combined = {}
            
            # Extract from schedule
            if schedule_data:
                schedule_info = schedule_data.get('data', schedule_data)
                route = []
                if isinstance(schedule_info, dict):
                    combined['trainNo'] = schedule_info.get('trainNumber', train_number)
                    combined['trainName'] = schedule_info.get('trainName', '')
                    # IRCTC schedule returns "route" list; filter stations where haltTime != 0
                    raw_route = schedule_info.get('route', schedule_info.get('stations', []))
                    for stop in raw_route or []:
                        halt = stop.get('haltTime') if isinstance(stop, dict) else None
                        try:
                            halt_val = float(halt) if halt is not None else 0
                        except Exception:
                            halt_val = 0
                        if halt_val != 0:
                            route.append(stop)
                    combined['route'] = route
                elif isinstance(schedule_info, list):
                    # Assume list of dicts with haltTime field
                    for stop in schedule_info:
                        halt = stop.get('haltTime') if isinstance(stop, dict) else None
                        try:
                            halt_val = float(halt) if halt is not None else 0
                        except Exception:
                            halt_val = 0
                        if halt_val != 0:
                            route.append(stop)
                    combined['route'] = route
            
            # Extract from status
            if status_data:
                status_info = status_data.get('data', status_data)
                if isinstance(status_info, dict):
                    combined['trainNo'] = status_info.get('train_number', combined.get('trainNo', train_number))
                    combined['trainName'] = status_info.get('train_name', combined.get('trainName', ''))
                    combined['currentStation'] = status_info.get('current_station_name', status_info.get('current_station', ''))
                    combined['delayMinutes'] = status_info.get('delay_in_departure', status_info.get('delayMinutes', 0))
                    combined['currentStationIndex'] = status_info.get('current_station_index', 0)
                    combined['status'] = status_info.get('train_status', status_info.get('status', 'Running'))
            
            print(f"[COMBINED] Route stations: {len(combined.get('route', []))}, Delay: {combined.get('delayMinutes', 0)} min")
            
            return jsonify({
                'success': True,
                'data': combined,
                'message': 'Train information retrieved successfully'
            }), 200
        
        # FALLBACK: Return sample data for testing
        print("[FALLBACK] Both APIs failed, returning sample data for demonstration")
        
        # Different sample data based on train number
        if train_number == '12084':
            sample_data = {
                'trainNo': train_number,
                'trainName': 'Coimbatore Jan Shatabdi Express',
                'delayMinutes': 5,
                'currentStation': 'Erode Junction',
                'currentStationIndex': 4,
                'route': [
                    {'stationName': 'Coimbatore Junction', 'platform': '5', 'arrivalTime': '---', 'departureTime': '7:15 AM', 'distanceFromSource': '0 km', 'haltMinutes': 5},
                    {'stationName': 'Tiruppur', 'platform': '1', 'arrivalTime': '8:05 AM', 'departureTime': '8:07 AM', 'distanceFromSource': '55 km', 'haltMinutes': 2},
                    {'stationName': 'Erode Junction', 'platform': '3', 'arrivalTime': '8:45 AM', 'departureTime': '8:50 AM', 'distanceFromSource': '100 km', 'haltMinutes': 5},
                    {'stationName': 'Karur', 'platform': '2', 'arrivalTime': '9:30 AM', 'departureTime': '9:32 AM', 'distanceFromSource': '165 km', 'haltMinutes': 2},
                    {'stationName': 'Tiruchchirappalli Junction', 'platform': '1', 'arrivalTime': '10:45 AM', 'departureTime': '11:00 AM', 'distanceFromSource': '230 km', 'haltMinutes': 15},
                    {'stationName': 'Thanjavur Junction', 'platform': '9', 'arrivalTime': '11:55 AM', 'departureTime': '12:05 PM', 'distanceFromSource': '280 km', 'haltMinutes': 10},
                    {'stationName': 'Kumbakonam', 'platform': '1', 'arrivalTime': '12:37 PM', 'departureTime': '12:39 PM', 'distanceFromSource': '319 km', 'haltMinutes': 2},
                    {'stationName': 'Mayiladuthurai Junction', 'platform': '4', 'arrivalTime': '1:15 PM', 'departureTime': '---', 'distanceFromSource': '350 km', 'haltMinutes': 0}
                ]
            }
        else:
            # Default sample data for other trains (12083 and others)
            sample_data = {
                'trainNo': train_number,
                'trainName': 'Jan Shatabdi Express',
                'delayMinutes': 16,
                'currentStation': 'Kumbakonam',
                'currentStationIndex': 1,
                'route': [
                    {'stationName': 'Mayiladuthurai Junction', 'platform': '4', 'arrivalTime': '---', 'departureTime': '3:12 PM', 'distanceFromSource': '0 km', 'haltMinutes': 5},
                    {'stationName': 'Kumbakonam', 'platform': '1', 'arrivalTime': '3:37 PM', 'departureTime': '3:39 PM', 'distanceFromSource': '31 km', 'haltMinutes': 2},
                    {'stationName': 'Thanjavur Junction', 'platform': '9', 'arrivalTime': '4:04 PM', 'departureTime': '4:20 PM', 'distanceFromSource': '70 km', 'haltMinutes': 16},
                    {'stationName': 'Tiruchchirappalli Junction', 'platform': '1', 'arrivalTime': '5:02 PM', 'departureTime': '5:25 PM', 'distanceFromSource': '120 km', 'haltMinutes': 23},
                    {'stationName': 'Erode Junction', 'platform': '3', 'arrivalTime': '7:30 PM', 'departureTime': '7:35 PM', 'distanceFromSource': '250 km', 'haltMinutes': 5},
                    {'stationName': 'Coimbatore Junction', 'platform': '5', 'arrivalTime': '9:00 PM', 'departureTime': '---', 'distanceFromSource': '350 km', 'haltMinutes': 0}
                ]
            }
        
        return jsonify({
            'success': True,
            'data': sample_data,
            'message': 'Train information (demo data)',
            'note': 'RailRadar API not responding - showing sample data for demonstration'
        }), 200
        
    except Exception as e:
        print(f"Error tracking train: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# Static file serving - MUST be at the end, after all API routes
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (HTML, CSS, JS, images)"""
    return app.send_static_file(filename)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Railway Complaint System - API Server")
    print("="*50)
    
    # Initialize MongoDB
    if not init_mongodb():
        print("⚠ Warning: MongoDB connection failed. Some features may not work.")
    
    # Load AI models
    print("\nLoading AI models...")
    models_ok = load_models()
    if not models_ok:
        print("⚠ Warning: Models failed to load. Classification endpoints may not work.")
    
    print("\nStarting Flask API server...")
    print("API running on: http://127.0.0.1:5000")
    print("="*50 + "\n")
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
    except Exception as e:
        print(f"Error running Flask app: {e}")
        import traceback
        traceback.print_exc()
