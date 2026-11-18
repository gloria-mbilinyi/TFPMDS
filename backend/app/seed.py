"""Idempotent illustrative demo data. Never resets or deletes user work."""
import argparse
from datetime import date

from sqlalchemy import select

from .db import SessionLocal, initialize
from .models import MarketPrice, Produce, PurchaseOrder, Shipment, User
from .security import passwords

DEMO_PASSWORD = 'DemoPass123!'
ACCOUNTS = [
    ('admin', 'Neema Mushi', 'administrator', 'Dodoma', 'Ministry demo office'),
    ('farmer', 'Asha Mbilinyi', 'farmer', 'Morogoro', 'Kilombero, Morogoro'),
    ('mbeya', 'Joseph Mwakyusa', 'farmer', 'Mbeya', 'Mbarali, Mbeya'),
    ('iringa', 'Rehema Mwakalinga', 'farmer', 'Iringa', 'Kilolo, Iringa'),
    ('mwanza', 'Peter Mabula', 'farmer', 'Mwanza', 'Magu, Mwanza'),
    ('arusha', 'Grace Mollel', 'farmer', 'Arusha', 'Meru, Arusha'),
    ('buyer', 'Juma Food Traders', 'buyer', 'Dar es Salaam', 'Kariakoo Market, Dar es Salaam'),
    ('buyer2', 'Upendo Foods', 'buyer', 'Dodoma', 'Central Market, Dodoma'),
    ('logistics', 'Baraka Kweka', 'logistics', 'Morogoro', 'Morogoro Distribution Centre'),
    ('transporter', 'Safari Fresh Transport', 'transporter', 'Morogoro', 'Morogoro Depot'),
    ('transporter2', 'Mwanza Produce Express', 'transporter', 'Mwanza', 'Mwanza Depot'),
]
PRODUCE = [
    ('farmer', 'Kilombero white rice', 'Rice', 2400, 2200, 'Aromatic milled rice, carefully dried and ready for bulk purchase.'),
    ('farmer', 'Morogoro yellow maize', 'Maize', 4200, 850, 'Clean maize grain from the Kilombero valley. Packed in 50 kg sacks.'),
    ('mbeya', 'Mbarali premium rice', 'Rice', 1800, 2400, 'Long-grain rice from Mbarali, available for wholesale collection.'),
    ('mbeya', 'Mbeya Irish potatoes', 'Potatoes', 3200, 1100, 'Sorted fresh potatoes for restaurants, markets and food processors.'),
    ('iringa', 'Iringa red kidney beans', 'Beans', 1500, 2800, 'Dry red beans, cleaned and graded for consistent quality.'),
    ('mwanza', 'Lake Zone tomatoes', 'Tomatoes', 900, 1500, 'Fresh ripe tomatoes. Arrange prompt pickup to preserve quality.'),
    ('arusha', 'Meru Hass avocados', 'Avocado', 1200, 2100, 'Firm Hass avocados suitable for local market distribution.'),
    ('iringa', 'Kilolo sunflower seed', 'Sunflower', 2100, 1300, 'Dried sunflower seed for local oil processors.'),
]


def seed(db):
    for index, (alias, name, role, region, location) in enumerate(ACCOUNTS):
        if db.scalar(select(User).where(User.email == f'{alias}@tfpmds.demo')) is None:
            db.add(User(name=name, email=f'{alias}@tfpmds.demo', password_hash=passwords.hash(DEMO_PASSWORD),
                        role=role, status='approved', phone=f'+25571234{index:04}', region=region, location=location,
                        farm_size_acres=8 if role == 'farmer' else 0,
                        crop_categories='Rice, Maize, Beans' if role == 'farmer' else '',
                        business_name=name if role in {'buyer','transporter'} else '', verification_note='Illustrative demo account.'))
    db.flush()
    for alias, name, crop, kg, price, description in PRODUCE:
        farmer = db.scalar(select(User).where(User.email == f'{alias}@tfpmds.demo'))
        if db.scalar(select(Produce).where(Produce.farmer_id == farmer.id, Produce.name == name)) is None:
            db.add(Produce(farmer_id=farmer.id, name=name, crop=crop, available_kg=kg, price_tzs=price,
                           description=description, harvest_date=date(2026,11,10)))
        if db.scalar(select(MarketPrice).where(MarketPrice.crop == crop, MarketPrice.region == farmer.region)) is None:
            db.add(MarketPrice(crop=crop, region=farmer.region, price_tzs=price,
                               observed_on=date(2026,11,18), source='Illustrative academic demo - not live market data'))
    db.commit()


def seed_transactions(db):
    from .orders import create, decide
    from .payments import initiate, simulate
    from .logistics import assign, progress
    from .schemas import Assign, Decision, OrderCreate, PaymentCreate, PaymentOutcome, ShipmentUpdate
    buyer=db.scalar(select(User).where(User.email=='buyer@tfpmds.demo'))
    officer=db.scalar(select(User).where(User.email=='logistics@tfpmds.demo'))
    driver=db.scalar(select(User).where(User.email=='transporter@tfpmds.demo'))
    for index, desired in enumerate(['in_transit','accepted','pending_farmer_approval'],1):
        key=f'seed-order-{index:04}'
        if db.scalar(select(PurchaseOrder).where(PurchaseOrder.idempotency_key==key)):
            continue
        product=db.scalar(select(Produce).where(Produce.name==PRODUCE[index-1][1]))
        farmer=db.get(User,product.farmer_id)
        order=create(OrderCreate(items=[{'produce_id':product.id,'quantity_kg':100+index*25}],
                                delivery_address=buyer.location),key,buyer,db)
        if desired!='pending_farmer_approval':
            decide(order['id'],Decision(action='accept'),farmer,db)
        if desired=='in_transit':
            payment=initiate(PaymentCreate(order_id=order['id'],provider='mpesa',phone=buyer.phone),f'seed-payment-{index:04}',buyer,db)
            simulate(payment['id'],PaymentOutcome(outcome='successful'),buyer,db)
            shipment=db.scalar(select(Shipment).where(Shipment.order_id==order['id']))
            assign(shipment.id,Assign(transporter_id=driver.id),officer,db)
            for status,location in [('ready_for_pickup','Kilombero'),('picked_up','Morogoro'),('in_transit','Chalinze')]:
                progress(shipment.id,ShipmentUpdate(status=status,location=location,note='Illustrative demo journey.'),driver,db)
        db.commit()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo',action='store_true',help='Explicitly create local demo credentials and simulated transactions.')
    args=parser.parse_args()
    if not args.demo:
        parser.error('Pass --demo to acknowledge these public demonstration credentials.')
    initialize()
    with SessionLocal() as db:
        seed(db); seed_transactions(db)
    print('Demo seeded. Password for all synthetic @tfpmds.demo accounts: '+DEMO_PASSWORD)
