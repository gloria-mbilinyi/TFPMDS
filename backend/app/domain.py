"""Shared workflow vocabulary for storage, API projections and editable UML."""
ORDER_STATES = (
    'pending_farmer_approval', 'accepted', 'awaiting_payment', 'paid',
    'processing_delivery', 'in_transit', 'delivered', 'completed',
    'rejected', 'cancelled', 'payment_failed', 'return_requested', 'returned',
)
SHIPMENT_TRANSITIONS = {
    'pending_arrangement': {'awaiting_transporter', 'assignment_failed'},
    'awaiting_transporter': {'assignment_failed'},
    'assignment_failed': {'awaiting_transporter'},
    'assigned': {'ready_for_pickup', 'assignment_failed'},
    'ready_for_pickup': {'picked_up', 'delivery_failed'},
    'picked_up': {'in_transit', 'delivery_failed'},
    'in_transit': {'delivered', 'delivery_failed'},
    'delivery_failed': {'ready_for_pickup', 'return_requested'},
    'delivered': {'return_requested'},
    'return_requested': {'returned'},
    'returned': set(),
}
ASSIGNABLE = {'pending_arrangement', 'awaiting_transporter', 'assignment_failed', 'assigned'}
