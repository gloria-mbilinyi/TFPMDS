"""Freeze the master brief's 61 functional acceptance requirements."""
import json
from pathlib import Path

CATALOGUE = {
    'A': ('Farmer registration', [
        'Farmer account registration', 'Farmer login and logout', 'Farmer profile management',
        'Farm location and size', 'Crop categories', 'Administrator verification',
        'Registration approval and rejection', 'Registration status notifications']),
    'B': ('Produce management', [
        'Add agricultural produce', 'Edit produce information', 'Delete or deactivate listings',
        'Specify available quantities', 'Specify expected prices', 'Specify harvest dates',
        'Display produce availability', 'Prevent invalid quantities and prices']),
    'C': ('Buyer management', [
        'Buyer registration', 'Buyer account approval', 'Buyer login', 'Buyer profile',
        'Search agricultural produce', 'Filter by crop, region, price and quantity', 'View farmer listings']),
    'D': ('Produce ordering', [
        'Buyer purchase order creation', 'Order validation', 'Farmer order notification',
        'Farmer acceptance or rejection', 'Order status management', 'Order history',
        'Quantity reservation and stock consistency']),
    'E': ('Payment processing', [
        'Mobile money payment initiation', 'M-Pesa simulation', 'Airtel Money simulation',
        'Tigo-Pesa simulation', 'Payment status verification', 'Transaction records',
        'Payment receipts', 'Failed and cancelled payment handling', 'Duplicate payment prevention']),
    'F': ('Logistics and delivery', [
        'Logistics officer dashboard', 'Delivery request after confirmed payment',
        'Transporter assignment', 'Transporter dashboard', 'Shipment status updates',
        'Shipment tracking history', 'Delivery confirmation', 'Farmer and buyer shipment tracking']),
    'G': ('Administration', [
        'Administrator dashboard', 'Farmer verification', 'Buyer approval', 'User management',
        'Transaction monitoring', 'Sales reporting', 'Market price management', 'Basic system analytics']),
    'H': ('Notifications', [
        'SMS notification simulation', 'In-app notifications', 'Order notifications',
        'Payment confirmation notifications', 'Delivery status notifications', 'Notification history']),
}

if __name__ == '__main__':
    target = Path(__file__).resolve().parents[1] / 'docs' / 'requirements.json'
    rows = [{'id': f'{module}{number:02}', 'module': title, 'requirement': description}
            for module, (title, items) in CATALOGUE.items()
            for number, description in enumerate(items, 1)]
    target.write_text(json.dumps(rows, indent=2) + '\n', encoding='utf-8')
    print(f'{len(rows)} individual master-brief functional requirements catalogued.')
