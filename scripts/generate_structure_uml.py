"""Editable behavioral and package/class models matching the implemented API."""
import sys
from pathlib import Path

from uml_canvas import Canvas, GREEN, MUTED
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.domain import SHIPMENT_TRANSITIONS


def state(c,name,x,y,description='',key=None):
    c.rect(x,y,230,82,name+('\n'+description if description else ''),size=16,bold=True,
           fill='#edf4e8',stroke='#809b7d',rounded=True,key=key)


def pseudo(c,x,y,final=False,key=None):
    if final:
        c.rect(x-17,y-17,34,34,kind='ellipse',fill='white',stroke=GREEN,key=key)
        c.rect(x-10,y-10,20,20,kind='ellipse',fill=GREEN,stroke=GREEN)
    else:c.rect(x-10,y-10,20,20,kind='ellipse',fill=GREEN,stroke=GREEN,key=key)


def flow(c,source,target,points,label,box):
    c.line(points,source=source,target=target)
    c.text(*box,label,size=13,color=GREEN)


def purchase_order():
    c=Canvas('purchase-order-state','PurchaseOrder behavioral state machine',2450,1600)
    c.header('TFPMDS | PurchaseOrder behavioral state machine','Events [guards] / actions. Created is a validation transient; persistent orders start PendingFarmerApproval only after all stock reservations succeed.')
    nodes={
      'created':('Created',150,290,'validation transient'),
      'pending_farmer_approval':('PendingFarmerApproval',600,290,'reserved stock'),
      'accepted':('Accepted',1050,290,'farmer approved'),
      'awaiting_payment':('AwaitingPayment',1500,290,'one pending attempt'),
      'paid':('Paid',1950,290,'receipt + shipment created'),
      'processing_delivery':('ProcessingDelivery',1950,650,'transporter assigned'),
      'in_transit':('InTransit',1500,650,'shipment in transit'),
      'delivered':('Delivered',1050,650,'transporter confirmed'),
      'completed':('Completed',600,650,'buyer confirmed receipt'),
      'rejected':('Rejected',600,1040,'stock released once'),
      'cancelled':('Cancelled',1050,1040,'stock released once'),
      'payment_failed':('PaymentFailed',1500,1040,'stock remains reserved'),
      'return_requested':('ReturnRequested',1950,1040,'explicit logistics exception'),
      'returned':('Returned',1950,1350,'goods returned; refund future'),
    }
    pseudo(c,75,331,key='initial')
    for key,(name,x,y,description) in nodes.items():state(c,name,x,y,description,key='state_'+key)
    pseudo(c,715,1210,True,key='final_rejected');pseudo(c,1165,1210,True,key='final_cancelled');pseudo(c,2310,1391,True,key='final_returned')
    def edge(a,b,points,label,box):flow(c,'state_'+a if a!='initial' else a,'state_'+b if not b.startswith('final') else b,points,label,box)
    edge('initial','created',[(85,331),(150,331)],'submitOrder',(55,245,180,35))
    edge('created','pending_farmer_approval',[(380,331),(600,331)],'[valid and stock sufficient]\n/ reserve all lines; persist',(390,250,205,76))
    edge('pending_farmer_approval','accepted',[(830,331),(1050,331)],'accept [responsible farmer]\n/ set accepted; notify buyer',(840,250,205,76))
    edge('accepted','awaiting_payment',[(1280,331),(1500,331)],'initiate [ordering buyer]\n/ store pending attempt',(1290,250,205,76))
    edge('awaiting_payment','paid',[(1730,331),(1950,331)],'confirm [successful, pending]\n/ receipt + shipment atomically',(1740,250,205,76))
    edge('paid','processing_delivery',[(2065,372),(2065,650)],'assign [authorized logistics,\napproved transporter]\n/ assignment and tracking event',(2095,460,310,100))
    edge('processing_delivery','in_transit',[(1950,691),(1730,691)],'progress [shipment picked_up]\n/ set in_transit; notify',(1740,610,205,76))
    edge('in_transit','delivered',[(1500,691),(1280,691)],'confirmDelivery [in_transit]\n/ delivered + tracking event',(1290,610,205,76))
    edge('delivered','completed',[(1050,691),(830,691)],'confirmReceipt [ordering buyer]\n/ complete order',(840,610,205,76))
    edge('pending_farmer_approval','rejected',[(600,360),(550,360),(550,1081),(600,1081)],'reject [responsible farmer]\n/ release reservations once',(255,1020,275,80))
    edge('pending_farmer_approval','cancelled',[(600,340),(520,340),(520,960),(1165,960),(1165,1040)],'cancel [ordering buyer]\n/ release reservations once',(710,925,415,60))
    edge('accepted','cancelled',[(1165,372),(1410,372),(1410,985),(1165,985),(1165,1040)],'cancel [no pending payment]\n/ release reservations',(1190,830,205,70))
    edge('awaiting_payment','payment_failed',[(1615,372),(1820,372),(1820,1081),(1730,1081)],'fail [pending attempt]\n/ no receipt or shipment',(1835,815,225,80))
    edge('payment_failed','awaiting_payment',[(1500,1081),(1450,1081),(1450,331),(1500,331)],'retry [buyer, new attempt]\n/ pending payment',(1460,460,245,85))
    edge('payment_failed','cancelled',[(1500,1081),(1280,1081)],'cancel [buyer]\n/ release reservations',(1290,1000,205,75))
    edge('awaiting_payment','accepted',[(1615,372),(1615,440),(1165,440),(1165,372)],'cancelPayment [pending attempt] / cancelled attempt; order accepted',(1165,440,420,65))
    edge('in_transit','processing_delivery',[(1615,650),(1615,555),(2065,555),(2065,650)],'recover [shipment delivery_failed] / explicit ready_for_pickup recovery',(1660,555,360,65))
    edge('delivered','return_requested',[(1165,732),(1165,865),(2065,865),(2065,1040)],'requestReturn [authorized logistics + reason] / exception workflow',(1210,865,610,60))
    edge('completed','return_requested',[(715,732),(715,790),(2120,790),(2120,1040)],'requestReturn [authorized logistics + reason] / reopen only as explicit return',(1100,745,700,45))
    edge('in_transit','return_requested',[(1615,732),(1615,905),(2065,905),(2065,1040)],'requestReturn [shipment delivery_failed, logistics] / explicit exception',(1500,925,650,65))
    edge('return_requested','returned',[(2065,1122),(2065,1350)],'confirmReturn [assigned transporter or logistics]\n/ append returned event; no automatic stock/refund',(2090,1190,305,100))
    edge('returned','final_returned',[(2180,1391),(2293,1391)],'close exception',(2185,1320,200,60))
    edge('rejected','final_rejected',[(715,1122),(715,1193)],'terminal',(740,1130,160,40))
    edge('cancelled','final_cancelled',[(1165,1122),(1165,1193)],'terminal',(1190,1130,160,40))
    c.text(45,1485,2350,70,'Validation failure creates no persistent order. Rejected/cancelled orders cannot be paid. Paid orders have no ordinary cancellation path. Delivery failure is a shipment exception; an order remains in its delivery state until explicit recovery or return. All compare-and-set transitions run in the request transaction.',size=16,color=MUTED)
    c.save()


def shipment():
    c=Canvas('shipment-state','Shipment behavioral state machine',2450,2150)
    c.header('TFPMDS | Shipment behavioral state machine','State edges use the exact graph in backend/app/domain.py. Numbered transition specifications below provide the events, guards and actions for every edge.')
    positions={'pending_arrangement':(130,280),'awaiting_transporter':(600,280),'assigned':(1070,280),'ready_for_pickup':(1540,280),'picked_up':(2010,280),
      'in_transit':(2010,680),'delivered':(1540,680),'assignment_failed':(600,1070),'delivery_failed':(1070,1070),'return_requested':(1540,1070),'returned':(2010,1070)}
    pseudo(c,65,321,key='initial');c.line([(75,321),(130,321)],source='initial',target='state_pending_arrangement')
    labels={
      ('pending_arrangement','awaiting_transporter'):'arrange [logistics] / await assignment',
      ('pending_arrangement','assignment_failed'):'record failure [logistics + reason] / append event',
      ('awaiting_transporter','assignment_failed'):'record failure [logistics + reason] / append event',
      ('assignment_failed','awaiting_transporter'):'retry arrangement [logistics] / append event',
      ('assigned','ready_for_pickup'):'prepare pickup [assigned driver or logistics] / append event',
      ('assigned','assignment_failed'):'record failure [logistics + reason] / clear driver',
      ('ready_for_pickup','picked_up'):'confirm pickup [authorized, driver assigned] / append event',
      ('ready_for_pickup','delivery_failed'):'report failure [authorized + reason] / append event',
      ('picked_up','in_transit'):'depart [authorized] / order in_transit + event',
      ('picked_up','delivery_failed'):'report failure [authorized + reason] / append event',
      ('in_transit','delivered'):'confirm delivery [authorized] / order delivered + notify',
      ('in_transit','delivery_failed'):'report failure [authorized + reason] / append event',
      ('delivery_failed','ready_for_pickup'):'recover [assigned driver or logistics] / order processing_delivery',
      ('delivery_failed','return_requested'):'request return [logistics + reason] / order return_requested',
      ('delivered','return_requested'):'request return [logistics + reason] / explicit exception',
      ('return_requested','returned'):'confirm return [authorized] / order returned + event',
    }
    edges=[]
    for source,targets in SHIPMENT_TRANSITIONS.items():
        for target in sorted(targets):edges.append((source,target,labels[(source,target)]))
    for source in ['pending_arrangement','awaiting_transporter','assignment_failed']:
        edges.append((source,'assigned','assign [logistics, paid order, approved driver] / set driver; notify'))
    # Reassignment is an intentional self transition exposed by the assignment API.
    edges.append(('assigned','assigned','reassign [logistics, paid order, approved driver] / change driver; notify'))
    for index,(source,target,label) in enumerate(edges,1):
        sx,sy=positions[source];tx,ty=positions[target];p=(sx+115,sy+41);q=(tx+115,ty+41)
        if sy==ty and source!=target:
            p=(sx+(230 if tx>sx else 0),sy+41);q=(tx+(0 if tx>sx else 230),ty+41);points=[p,q]
        elif sx==tx and source!=target:
            p=(sx+115,sy+(82 if ty>sy else 0));q=(tx+115,ty+(0 if ty>sy else 82));points=[p,q]
        elif source==target:points=[(sx+185,sy),(sx+185,sy-95),(sx+45,sy-95),(sx+45,sy)]
        else:
            lane=450+(index%5)*38
            points=[(sx+115,sy+82),(sx+115,lane),(tx+115,lane),(tx+115,ty)]
        c.line(points,f'T{index:02}',size=14,source='state_'+source,target='state_'+target)
    for key,(x,y) in positions.items():state(c,''.join(w.title() for w in key.split('_')),x,y,key= 'state_'+key)
    pseudo(c,2350,1111,True,key='final_returned');c.line([(2240,1111),(2333,1111)],source='state_returned',target='final_returned')
    c.text(45,1200,2350,70,'Delivered is stable for normal operation. Its only outgoing edge is an explicit logistics return with a required reason. Returned is terminal. The local application creates a shipment only when a simulated payment is successful.',size=16,color=MUTED)
    for index,(source,target,label) in enumerate(edges,1):
        col=(index-1)%2;row=(index-1)//2
        c.rect(45+col*1200,1310+row*66,1160,60,f'T{index:02}  {source} → {target}\n{label}',fill='#f2f6ef' if row%2==0 else 'white',stroke='white',size=14,align='left')
    c.save()


def package_overview():
    c=Canvas('package-overview','Architecture package overview',2180,1370)
    c.header('TFPMDS | Package architecture','Conceptual package ownership mapped to concrete Python modules. Dashed open-arrow dependencies form a directed acyclic graph; persistence does not import application modules.')
    positions={
      'FarmerManagement':(70,180),'BuyerManagement':(70,400),'ProduceManagement':(70,620),'OrderManagement':(70,840),
      'PaymentManagement':(590,180),'LogisticsManagement':(590,400),'Administration':(590,620),'Reporting':(590,840),
      'Authentication':(1180,230),'NotificationManagement':(1180,650),'Persistence':(1770,230),'ExternalIntegrations':(1770,650),
    }
    modules={'FarmerManagement':'users.py + auth.register','BuyerManagement':'users.py + marketplace.py','ProduceManagement':'produce.py','OrderManagement':'orders.py',
      'PaymentManagement':'payments.py','LogisticsManagement':'logistics.py + domain.py','Administration':'users.py admin routes','Reporting':'reporting.py',
      'Authentication':'auth.py + security.py','NotificationManagement':'notifications.py + notification_api.py','Persistence':'models.py + db.py','ExternalIntegrations':'integrations.py protocols / mocks'}
    deps={
      'FarmerManagement':['Authentication','NotificationManagement','Persistence'],
      'BuyerManagement':['Authentication','Persistence'], 'ProduceManagement':['Authentication','Persistence'],
      'OrderManagement':['Authentication','NotificationManagement','Persistence'],
      'PaymentManagement':['OrderManagement','ExternalIntegrations','NotificationManagement','Persistence'],
      'LogisticsManagement':['OrderManagement','Authentication','NotificationManagement','Persistence'],
      'Administration':['Authentication','NotificationManagement','Persistence'], 'Reporting':['Authentication','Persistence'],
      'Authentication':['Persistence'],'NotificationManagement':['ExternalIntegrations','Persistence'],
    }
    import json
    from uml_canvas import OUT
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/'package-dependencies.json').write_text(json.dumps(deps,indent=2)+'\n',encoding='utf-8')
    for source,targets in deps.items():
        sx,sy=positions[source]
        for target in targets:
            tx,ty=positions[target]
            c.line([(sx+310,sy+80),(tx,ty+80)],dashed=True,arrow='open',source='package_'+source,target='package_'+target,color='#afbbad')
    for name,(x,y) in positions.items():
        c.rect(x,y,330,150,name,kind='package',fill='#f4f7ee',size=16,bold=True,key='package_'+name)
        c.text(x+12,y+58,305,70,modules[name],size=14,color=MUTED)
    c.text(60,1080,2030,65,'The React/TypeScript interface calls these application boundaries through REST. A package is a responsibility boundary, not necessarily a separate Python directory. All application dependencies point toward shared guards, persistence or provider ports.',size=18,color=MUTED)
    c.text(60,1180,2030,120,'Infrastructure note: SQLite sessions enable foreign keys and rollback failures. Stock reservations use conditional UPDATE statements. PostgreSQL requires a driver, schema migrations, deployment configuration and integration testing before use; no PostgreSQL deployment is claimed.',size=17,color=MUTED)
    c.save()


def class_box(c,name,x,y,attributes,operations=(),width=340,key=None):
    h=65+len(attributes)*26+(35+len(operations)*26 if operations else 0)
    c.rect(x,y,width,h,fill='#ffffff',stroke='#8fa58c',key=key or 'class_'+name)
    c.rect(x,y,width,46,name,fill='#eaf2e3',stroke='#8fa58c',size=17,bold=True)
    c.text(x+10,y+53,width-20,len(attributes)*26,'\n'.join(attributes),size=14)
    if operations:
        sy=y+65+len(attributes)*26
        c.line([(x,sy-7),(x+width,sy-7)],arrow='none',color='#c7d2bd')
        c.text(x+10,sy,width-20,len(operations)*26,'\n'.join(operations),size=14)
    return (x,y,width,h)


def relationship(c,a,b,label,points=None,composition=False,aggregation=False,dashed=False,box=None):
    ax,ay,aw,ah=a;bx,by,bw,bh=b
    points=points or [(ax+aw,ay+ah/2),(bx,by+bh/2)]
    c.line(points,label,dashed=dashed,arrow='open' if dashed else 'none',
           start_arrow='diamond' if composition else 'diamondThin' if aggregation else None,label_box=box,size=14)


def identity_classes():
    c=Canvas('classes-identity-produce','Identity and marketplace detailed packages',2040,1420)
    c.header('TFPMDS | Identity and marketplace packages','Role projections are conceptual views of the single User model, not extra ORM tables or invented Python subclasses. Operations below belong to the named implemented services.')
    c.rect(35,145,600,1130,'Authentication / Persistence',kind='frame',fill='none',size=20)
    c.rect(665,145,620,1130,'FarmerManagement / BuyerManagement',kind='frame',fill='none',size=20)
    c.rect(1315,145,690,1130,'ProduceManagement',kind='frame',fill='none',size=20)
    user=class_box(c,'User',105,215,['+ id: int {PK}','+ email: str {unique}','+ password_hash: str','+ role: Role','+ status: ApprovalStatus','+ active: bool','+ name, phone, region: str','+ location: str','+ farm_size_acres: int','+ crop_categories: str','+ business_name: str','+ verification_note: str'],width=440)
    auth=class_box(c,'AuthenticationService',105,730,['«module» auth.py / security.py'],['+ register(data)','+ login(data)','+ me(user)','+ logout(user)','+ authorize(user, roles)'],width=440)
    roles=[]
    for index,(name,attributes) in enumerate([
      ('Farmer',['«role projection» role = farmer','+ location, farm_size_acres','+ crop_categories']),
      ('Buyer',['«role projection» role = buyer','+ business_name, location']),
      ('Administrator',['«role projection» role = administrator']),
      ('LogisticsOfficer',['«role projection» role = logistics']),
      ('Transporter',['«role projection» role = transporter']),
    ]):
        y=215+index*195
        role=class_box(c,name,765,y,attributes,width=420)
        relationship(c,user,role,'role view',dashed=True,points=[(545,280+index*65),(765,y+55)])
        roles.append(role)
    produce=class_box(c,'Produce',1420,215,['+ id: int {PK}','+ farmer_id: int {FK User}','+ name, crop, description: str','+ available_kg: int >= 0','+ price_tzs: int > 0','+ harvest_date: date','+ active: bool'],width=470)
    service=class_box(c,'ProduceService',1420,560,['«module» produce.py / marketplace.py'],['+ create(data, farmer)','+ edit(id, data, owner)','+ deactivate(id, owner)','+ search(filters)','+ detail(id)'],width=470)
    market=class_box(c,'MarketPrice',1420,935,['+ id: int {PK}','+ crop, region: str {unique pair}','+ price_tzs: int > 0','+ observed_on: date','+ source: str'],width=470)
    relationship(c,roles[0],produce,'1 farmer  —  0..* listings',box=(1210,365,225,65))
    relationship(c,service,produce,'uses',dashed=True,points=[(1655,560),(1655,produce[1]+produce[3])],box=(1680,490,175,50))
    relationship(c,auth,user,'uses',dashed=True,points=[(325,730),(325,user[1]+user[3])],box=(345,665,175,50))
    c.text(50,1310,1940,80,'Farmer/Buyer profiles are not public API projections. Marketplace responses expose only farmer name, region and farm location. Staff accounts cannot be publicly registered. Administrator approval and role guards load current database values on each request.',size=17,color=MUTED)
    c.save()


def transaction_classes():
    c=Canvas('classes-orders-payments','Ordering and payment detailed packages',2130,1400)
    c.header('TFPMDS | Orders and simulated payments','Monetary totals use BIGINT integer TZS. Every order contains at least one line from one farmer. Relationships state the implemented cardinality and lifecycle ownership.')
    c.rect(35,145,980,1130,'OrderManagement',kind='frame',fill='none',size=20)
    c.rect(1050,145,1045,1130,'PaymentManagement / ExternalIntegrations',kind='frame',fill='none',size=20)
    order=class_box(c,'PurchaseOrder',90,215,['+ id: int {PK}','+ buyer_id, farmer_id: int {FK User}','+ status: OrderState','+ total_tzs: bigint > 0','+ delivery_address: str','+ idempotency_key: str','+ fingerprint: str','{unique buyer_id, idempotency_key}'],width=510)
    item=class_box(c,'OrderItem',90,660,['+ id: int {PK}','+ order_id: int {FK PurchaseOrder}','+ produce_id: int {FK Produce}','+ quantity_kg: int > 0','+ unit_price_tzs: int > 0','+ produce_name: str {snapshot}'],width=510)
    service=class_box(c,'OrderService',650,215,['«module» orders.py'],['+ create(data, key, buyer, db)','+ decide(id, decision, user, db)','+ transition(db, expected, next)','+ history(user)'],width=310)
    payment=class_box(c,'Payment',1120,215,['+ id: int {PK}','+ order_id, buyer_id: int {FK}','+ provider: ProviderName','+ amount_tzs: bigint > 0','+ status: PaymentStatus','+ reference: str {unique}','+ idempotency_key: str','{unique buyer_id, idempotency_key}'],width=490)
    receipt=class_box(c,'PaymentReceipt',1660,680,['+ id: int {PK}','+ payment_id: int {unique FK}','+ order_id: int {unique FK}','+ number: str {unique}','+ amount_tzs: bigint','+ created_at: datetime'],width=380)
    payservice=class_box(c,'PaymentService',1120,680,['«module» payments.py'],['+ initiate(data, key, buyer, db)','+ apply_outcome(db, payment, outcome)','+ callback(data, secret)','+ simulate(id, outcome, owner)','+ receipt(id, party)'],width=490)
    provider=class_box(c,'MobileMoneyProvider',1120,1080,['«protocol» integrations.py'],['+ initiate(amount_tzs, phone, provider)'],width=490)
    relationship(c,order,item,'1  ◆ contains  1..*',composition=True,points=[(345,order[1]+order[3]),(345,660)],box=(360,570,255,65))
    relationship(c,order,payment,'1 order — 0..* payment attempts',points=[(600,370),(620,370),(620,600),(1080,600),(1080,370),(1120,370)],box=(700,535,375,60))
    relationship(c,payment,receipt,'1 payment — 0..1 receipt',points=[(1500,payment[1]+payment[3]),(1850,680)],box=(1630,570,350,65))
    relationship(c,payservice,provider,'depends on interface',dashed=True,points=[(1365,payservice[1]+payservice[3]),(1365,1080)],box=(1400,1010,300,55))
    c.text(70,1300,2000,65,'Composition is used only for OrderItem ownership (ORM delete-orphan). A receipt is a unique associated record, not an invented cascading relationship. MockMobileMoney implements MobileMoneyProvider for mpesa, airtel_money and tigo_pesa; no real provider is called.',size=16,color=MUTED)
    c.save()


def logistics_classes():
    c=Canvas('classes-logistics-notifications','Logistics and notification detailed packages',2130,1430)
    c.header('TFPMDS | Logistics and notification packages','Tracking is append-only through workflow services. Notifications persist in the same business transaction. The mock SMS port creates references and sends no real network messages.')
    c.rect(35,145,1000,1160,'LogisticsManagement',kind='frame',fill='none',size=20)
    c.rect(1070,145,1025,1160,'NotificationManagement / ExternalIntegrations',kind='frame',fill='none',size=20)
    shipment=class_box(c,'Shipment',90,220,['+ id: int {PK}','+ order_id: int {unique FK PurchaseOrder}','+ transporter_id: int? {FK User}','+ tracking_code: str {unique}','+ status: ShipmentState'],width=490)
    event=class_box(c,'TrackingEvent',90,700,['+ id: int {PK}','+ shipment_id: int {FK Shipment}','+ actor_id: int {FK User}','+ status, location, note: str','+ created_at: datetime'],width=490)
    service=class_box(c,'LogisticsService',640,220,['«module» logistics.py'],['+ list_shipments(user)','+ assign(id, driver, staff)','+ progress(id, state, actor)','+ detail(id, party)','+ log_event(db, shipment, actor)'],width=330)
    driver=class_box(c,'Transporter',640,750,['«User role view»','+ id: int','+ role = transporter','+ active, status'],width=330)
    notice=class_box(c,'Notification',1140,220,['+ id: int {PK}','+ user_id: int {FK User}','+ kind, message: str','+ read: bool','+ sms_status = simulated','+ sms_reference: str','+ created_at: datetime'],width=490)
    notifyservice=class_box(c,'NotificationService',1140,700,['«modules» notifications.py','notification_api.py'],['+ notify(db, user, kind, message)','+ history(user, unread_only)','+ mark_read(id, recipient)','+ read_all(user)','+ sms_log(administrator)'],width=490)
    sms=class_box(c,'SmsProvider',1690,700,['«protocol» integrations.py'],['+ send(phone, message): reference'],width=340)
    mock=class_box(c,'MockSms',1690,1030,['+ sends_real_sms = false'],['+ send(phone, message)'],width=340)
    relationship(c,shipment,event,'1  ◆ contains  1..* events',composition=True,points=[(335,shipment[1]+shipment[3]),(335,700)],box=(355,530,310,70))
    relationship(c,shipment,driver,'0..* shipments — 0..1 assigned driver',points=[(580,390),(805,750)],box=(600,570,410,65))
    relationship(c,notifyservice,notice,'persists history',dashed=True,points=[(1385,700),(1385,notice[1]+notice[3])],box=(1410,610,250,55))
    relationship(c,notifyservice,sms,'uses interface',dashed=True,box=(1590,600,430,50))
    relationship(c,mock,sms,'implements',dashed=True,points=[(1860,1030),(1860,sms[1]+sms[3])],box=(1880,940,175,60))
    c.text(65,1330,2000,65,'Shipment: one PurchaseOrder maps to zero or one Shipment; a shipment has one order. Notification: one User has zero or more notifications, each notification has one recipient. Transporter and LogisticsOfficer are authorized User role views, not separate account tables.',size=16,color=MUTED)
    c.save()


if __name__=='__main__':
    purchase_order();shipment();package_overview();identity_classes();transaction_classes();logistics_classes()
    print('Generated 2 state machines, 1 overview package diagram and 3 detailed package/class diagrams, with editable XML and PNGs.')
