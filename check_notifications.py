from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['railway_complaints']

# Check theft_lost_reports
print('=== Theft/Lost Reports ===')
reports = list(db.theft_lost_reports.find().limit(5))
for r in reports:
    report_id = r.get('_id')
    email = r.get('email')
    print(f'Report ID: {report_id}')
    print(f'  Email: {email}')
    print()

# Check notifications for Lost/Theft
print('=== Notifications for Lost/Theft ===')
notifs = list(db.notifications.find({'department': 'Lost/Theft'}).limit(5))
print(f'Total notifications found: {len(notifs)}')
for n in notifs:
    notif_id = n.get('_id')
    dept = n.get('department')
    report_or_complaint = n.get('report_id') or n.get('complaint_id')
    print(f'Notification ID: {notif_id}')
    print(f'  Department: {dept}')
    print(f'  Report/Complaint ID: {report_or_complaint}')
    print()
