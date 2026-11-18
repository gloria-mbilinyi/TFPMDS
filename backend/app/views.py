"""Public response projections. Never expose password hashes or private profiles."""
from .domain import SHIPMENT_TRANSITIONS
def fields(obj, *names):
    return {name: getattr(obj, name) for name in names}


def produce_view(record, farmer):
    return {**fields(record, 'id', 'farmer_id', 'name', 'crop', 'description', 'available_kg', 'price_tzs', 'harvest_date', 'active', 'created_at'),
            'farmer_name': farmer.name, 'region': farmer.region, 'location': farmer.location}


def order_view(record):
    return {**fields(record, 'id', 'buyer_id', 'farmer_id', 'status', 'total_tzs', 'delivery_address', 'note', 'created_at'),
            'buyer_name': record.buyer.name, 'farmer_name': record.farmer.name,
            'items': [fields(item, 'id', 'produce_id', 'produce_name', 'quantity_kg', 'unit_price_tzs') for item in record.items]}


def payment_view(record):
    return fields(record, 'id', 'order_id', 'provider', 'amount_tzs', 'status', 'reference', 'created_at')


def shipment_view(record):
    return {**fields(record, 'id', 'order_id', 'transporter_id', 'status', 'tracking_code', 'created_at'),
            'transporter_name': record.transporter.name if record.transporter else None,
            'next_states': sorted(SHIPMENT_TRANSITIONS[record.status]),
            'farmer_name': record.order.farmer.name, 'buyer_name': record.order.buyer.name,
            'pickup': record.order.farmer.location or record.order.farmer.region,
            'destination': record.order.delivery_address,
            'history': [fields(event, 'id', 'actor_id', 'status', 'location', 'note', 'created_at') for event in record.history]}
