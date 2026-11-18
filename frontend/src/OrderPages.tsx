import { useRef, useState, type FormEvent } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  CreditCard,
  Download,
  RefreshCw,
  ShieldCheck,
  Truck,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { date, human, money, post } from "./api";
import {
  Badge,
  Empty,
  ErrorBox,
  Loading,
  PageTitle,
  Success,
  useData,
} from "./components";
import { useSession } from "./session";
import type { Order, Payment, Receipt, Shipment } from "./types";

export function Orders() {
  const { user } = useSession();
  const orders = useData<Order[]>("/orders"),
    payments = useData<Payment[]>("/payments"),
    shipments = useData<Shipment[]>("/shipments");
  const [error, setError] = useState(""),
    [success, setSuccess] = useState(""),
    [busy, setBusy] = useState(false);
  async function decide(id: number, action: string, note: string) {
    setBusy(true);
    setError("");
    try {
      await post(`/orders/${id}/decision`, { action, note });
      setSuccess(`Order #${id} updated.`);
      await orders.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="TRADE WITH CONFIDENCE"
        title={user?.role === "farmer" ? "Farm orders" : "Purchase orders"}
        description="Review requests, follow payments and keep track of your trading history."
        actions={
          <Link className="btn primary" to="/marketplace">
            Browse produce
            <ArrowRight size={15} />
          </Link>
        }
      />
      <ErrorBox
        message={error || orders.error || payments.error || shipments.error}
      />
      {success && <Success>{success}</Success>}
      {orders.loading ? (
        <Loading />
      ) : !orders.data?.length ? (
        <Empty>No orders yet. Browse the marketplace to get started.</Empty>
      ) : (
        <div className="stack">
          {orders.data.map((o) => (
            <OrderCard
              key={o.id}
              order={o}
              payment={payments.data?.find(
                (p) => p.order_id === o.id && p.status === "successful",
              )}
              shipment={shipments.data?.find((s) => s.order_id === o.id)}
              busy={busy}
              decide={decide}
            />
          ))}
        </div>
      )}
    </>
  );
}
function OrderCard({
  order: o,
  payment,
  shipment,
  busy,
  decide,
}: {
  order: Order;
  payment?: Payment;
  shipment?: Shipment;
  busy: boolean;
  decide: (id: number, action: string, note: string) => void;
}) {
  const { user } = useSession();
  const [note, setNote] = useState("");
  return (
    <article className="panel order-card">
      <div className="section-heading">
        <div>
          <h2>Order #{String(o.id).padStart(4, "0")}</h2>
          <p className="muted">
            {date(o.created_at)} · {o.buyer_name} → {o.farmer_name}
          </p>
        </div>
        <Badge status={o.status} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Produce</th>
              <th>Quantity</th>
              <th>Price / kg</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            {o.items.map((i) => (
              <tr key={i.id}>
                <td>
                  <strong>{i.produce_name}</strong>
                </td>
                <td>{money(i.quantity_kg)} kg</td>
                <td>TZS {money(i.unit_price_tzs)}</td>
                <td>TZS {money(i.quantity_kg * i.unit_price_tzs)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="order-summary">
        <span>Delivery: {o.delivery_address}</span>
        <strong>Total: TZS {money(o.total_tzs)}</strong>
      </div>
      {o.note && <p className="muted">Note: {o.note}</p>}
      <div className="order-actions">
        {user?.id === o.farmer_id && o.status === "pending_farmer_approval" && (
          <>
            <label className="decision-note">
              Note to buyer
              <input
                aria-label={`Note for order ${o.id}`}
                maxLength={300}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Optional reason or pickup instructions"
              />
            </label>
            <button
              disabled={busy}
              className="btn primary"
              onClick={() => decide(o.id, "accept", note)}
            >
              Accept order
            </button>
            <button
              disabled={busy}
              className="btn danger"
              onClick={() => decide(o.id, "reject", note)}
            >
              Reject order
            </button>
          </>
        )}
        {user?.id === o.buyer_id &&
          ["accepted", "payment_failed", "awaiting_payment"].includes(
            o.status,
          ) && (
            <Link className="btn primary" to={`/payments/order/${o.id}`}>
              <CreditCard size={15} />
              {o.status === "awaiting_payment"
                ? "Continue payment"
                : "Simulate payment"}
            </Link>
          )}
        {user?.id === o.buyer_id &&
          ["pending_farmer_approval", "accepted", "payment_failed"].includes(
            o.status,
          ) && (
            <button
              disabled={busy}
              className="btn outline"
              onClick={() => decide(o.id, "cancel", "Cancelled by buyer.")}
            >
              Cancel order
            </button>
          )}
        {user?.id === o.buyer_id && o.status === "delivered" && (
          <button
            disabled={busy}
            className="btn primary"
            onClick={() =>
              decide(o.id, "complete", "Buyer confirmed receipt of delivery.")
            }
          >
            <CheckCircle2 size={15} />
            Confirm receipt & complete
          </button>
        )}
        {payment && (
          <Link className="btn outline" to={`/receipts/${payment.id}`}>
            View receipt
            <ArrowRight size={14} />
          </Link>
        )}
        {shipment && (
          <Link className="btn outline" to={`/tracking/${shipment.id}`}>
            <Truck size={15} />
            Track shipment
          </Link>
        )}
      </div>
    </article>
  );
}

export function PaymentPage() {
  const { orderId } = useParams(),
    { user } = useSession();
  const order = useData<Order>("/orders/" + orderId),
    payments = useData<Payment[]>("/payments");
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const key = useRef(crypto.randomUUID());
  const lastBody = useRef("");
  const payment = payments.data
    ?.filter((p) => p.order_id === Number(orderId))
    .sort((a, b) => b.id - a.id)[0];
  async function initiate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const form = new FormData(e.currentTarget);
    const body = {
      order_id: Number(orderId),
      provider: form.get("provider"),
      phone: form.get("phone"),
    };
    const text = JSON.stringify(body);
    if (lastBody.current && lastBody.current !== text)
      key.current = crypto.randomUUID();
    lastBody.current = text;
    try {
      await post("/payments", body, key.current);
      await Promise.all([order.reload(), payments.reload()]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function simulate(outcome: string) {
    if (!payment) return;
    setError("");
    setBusy(true);
    try {
      await post(`/payments/${payment.id}/simulate`, { outcome });
      if (outcome !== "successful") key.current = crypto.randomUUID();
      await Promise.all([order.reload(), payments.reload()]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="LOCAL DEMONSTRATION"
        title="Mobile money simulation"
        description="Try the payment workflow. No funds are moved and no PIN is ever required."
      />
      <ErrorBox message={error || order.error || payments.error} />
      {order.loading || payments.loading ? (
        <Loading />
      ) : (
        order.data && (
          <section className="panel narrow">
            <div className="simulation-banner">
              <ShieldCheck size={21} />
              <div>
                <strong>Simulation only</strong>
                <p>
                  These outcomes are generated locally. Do not enter a real
                  mobile money PIN.
                </p>
              </div>
            </div>
            <div className="order-summary">
              <span>Order #{order.data.id}</span>
              <strong>TZS {money(order.data.total_tzs)}</strong>
            </div>
            {payment?.status === "successful" ? (
              <>
                <Success>
                  Payment confirmed. A receipt and delivery request have been
                  created.
                </Success>
                <Link className="btn primary" to={`/receipts/${payment.id}`}>
                  View payment receipt
                  <ArrowRight size={15} />
                </Link>
              </>
            ) : payment?.status === "pending" ? (
              <>
                <p className="detail-description">
                  Simulated request initiated with {human(payment.provider)}.
                </p>
                <div className="reference">
                  Reference <strong>{payment.reference}</strong>
                </div>
                <div className="form-actions wrap">
                  <button
                    disabled={busy}
                    className="btn primary"
                    onClick={() => simulate("successful")}
                  >
                    Simulate success
                  </button>
                  <button
                    disabled={busy}
                    className="btn danger"
                    onClick={() => simulate("failed")}
                  >
                    Simulate failure
                  </button>
                  <button
                    disabled={busy}
                    className="btn outline"
                    onClick={() => simulate("cancelled")}
                  >
                    Cancel simulated payment
                  </button>
                </div>
              </>
            ) : user?.id === order.data.buyer_id &&
              ["accepted", "payment_failed"].includes(order.data.status) ? (
              <>
                <p className="detail-description">
                  {payment
                    ? `Previous attempt: ${human(payment.status)}. You may try again.`
                    : "The farmer accepted your order. Select a simulated provider below."}
                </p>
                <form onSubmit={initiate}>
                  <div className="form-grid">
                    <label>
                      Mobile money provider
                      <select name="provider">
                        <option value="mpesa">M-Pesa</option>
                        <option value="airtel_money">Airtel Money</option>
                        <option value="tigo_pesa">Tigo-Pesa</option>
                      </select>
                    </label>
                    <label>
                      Demo mobile number
                      <input
                        name="phone"
                        defaultValue={user.phone}
                        required
                        pattern="\+255[67][0-9]{8}"
                        placeholder="+255712345678"
                      />
                    </label>
                  </div>
                  <button disabled={busy} className="btn primary">
                    <CreditCard size={15} />
                    {busy ? "Initiating…" : "Initiate simulation"}
                  </button>
                </form>
              </>
            ) : (
              <p className="detail-description">
                Payment is available to the buyer after farmer acceptance.
                Current state: {human(order.data.status)}.
              </p>
            )}
            <div className="mt">
              <Link to="/orders" className="text-link">
                <ArrowLeft size={14} />
                Back to orders
              </Link>
            </div>
          </section>
        )
      )}
    </>
  );
}

export function ReceiptPage() {
  const { paymentId } = useParams();
  const { data, error, loading } = useData<Receipt>(
    `/payments/${paymentId}/receipt`,
  );
  return (
    <>
      <PageTitle
        title="Payment receipt"
        description="Your record of a successful simulated transaction."
        actions={
          <button
            className="btn outline no-print"
            onClick={() => window.print()}
          >
            <Download size={16} />
            Print / Save PDF
          </button>
        }
      />
      <ErrorBox message={error} />
      {loading ? (
        <Loading />
      ) : (
        data && (
          <article className="receipt">
            <div className="receipt-header">
              <div>
                <p className="eyebrow">TFPMDS</p>
                <h2>Payment receipt</h2>
                <small>{data.number}</small>
              </div>
              <Badge status="successful" />
            </div>
            <div className="receipt-total">
              <small>SIMULATED PAYMENT RECEIVED</small>
              <strong>TZS {money(data.amount_tzs)}</strong>
            </div>
            <dl>
              <dt>Order</dt>
              <dd>#{data.order_id}</dd>
              <dt>Buyer</dt>
              <dd>{data.buyer_name}</dd>
              <dt>Farmer</dt>
              <dd>{data.farmer_name}</dd>
              <dt>Provider</dt>
              <dd>{human(data.provider)}</dd>
              <dt>Date</dt>
              <dd>{date(data.created_at)}</dd>
              <dt>Reference</dt>
              <dd>{data.reference}</dd>
              <dt>Currency</dt>
              <dd>{data.currency}</dd>
            </dl>
            <p className="fine-print">
              {data.mode}. This receipt demonstrates the academic payment
              workflow and is not evidence of a real transfer.
            </p>
            <Link to="/orders" className="btn outline no-print mt">
              Back to orders
              <ArrowRight size={14} />
            </Link>
          </article>
        )
      )}
    </>
  );
}
