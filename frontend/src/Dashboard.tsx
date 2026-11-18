import {
  ArrowRight,
  Leaf,
  Package,
  ShoppingBag,
  Truck,
  TrendingUp,
  MapPin,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useSession } from "./session";
import { date, human, money } from "./api";
import {
  Badge,
  ErrorBox,
  Metric,
  PageTitle,
  ProduceCard,
  useData,
} from "./components";
import type { MarketPrice, Order, Payment, Produce, Shipment } from "./types";

export function Dashboard() {
  const { user } = useSession();
  const orders = useData<Order[]>("/orders"),
    payments = useData<Payment[]>("/payments"),
    shipments = useData<Shipment[]>("/shipments"),
    produce = useData<Produce[]>(
      user?.role === "farmer" ? "/produce/mine" : "/produce",
    ),
    prices = useData<MarketPrice[]>("/market-prices");
  if (!user) return null;
  const total = (payments.data || [])
    .filter((p) => p.status === "successful")
    .reduce((sum, p) => sum + p.amount_tzs, 0);
  const firstName = user.name.split(" ")[0];
  return (
    <>
      <PageTitle
        eyebrow="YOUR WORKSPACE"
        title={`Good ${new Date().getHours() < 12 ? "morning" : new Date().getHours() < 17 ? "afternoon" : "evening"}, ${firstName}`}
        description={`Here's what's happening in your ${human(user.role).toLowerCase()} workspace.`}
        actions={
          <span className="date-label">{date(new Date().toISOString())}</span>
        }
      />
      <section className="dashboard-hero">
        <div>
          <span className="eyebrow">GROWING OPPORTUNITIES, TOGETHER</span>
          <h2>
            Your harvest.
            <br />A wider market.
          </h2>
          <p>
            Connect with verified trading partners and follow every order from
            farm to delivery.
          </p>
          <Link to="/marketplace" className="btn cream">
            Explore the marketplace
            <ArrowRight size={16} />
          </Link>
        </div>
        <div className="hero-landscape" aria-hidden="true">
          <div className="sun" />
          <div className="hill one" />
          <div className="hill two" />
          <Leaf className="hero-leaf" />
          <span>Rooted in Tanzania.</span>
        </div>
      </section>
      <div className="metrics">
        <Metric
          icon={<ShoppingBag />}
          label="Purchase orders"
          value={money(orders.data?.length || 0)}
          note="Orders visible to your account"
        />
        <Metric
          icon={<TrendingUp />}
          label="Simulated trade value"
          value={`TZS ${money(total)}`}
          note="Successful simulated payments"
        />
        <Metric
          icon={<Package />}
          label="Available listings"
          value={money(produce.data?.filter((p) => p.active).length || 0)}
          note={
            user.role === "farmer"
              ? "Your farm listings"
              : "Verified marketplace listings"
          }
        />
        <Metric
          icon={<Truck />}
          label="Active shipments"
          value={money(
            shipments.data?.filter(
              (s) => !["delivered", "returned"].includes(s.status),
            ).length || 0,
          )}
          note="Arrangements and deliveries"
        />
      </div>
      <ErrorBox
        message={
          orders.error || payments.error || produce.error || shipments.error
        }
      />
      <div className="dashboard-columns">
        <section className="panel">
          <div className="section-heading">
            <div>
              <h2>Recent orders</h2>
              <p className="muted">Your latest trading activity</p>
            </div>
            <ShoppingBag size={20} />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Produce</th>
                  <th>Value</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.data?.slice(0, 5).map((o) => (
                  <tr key={o.id}>
                    <td>
                      <strong>#{String(o.id).padStart(4, "0")}</strong>
                      <small>{date(o.created_at)}</small>
                    </td>
                    <td>
                      {o.items[0]?.produce_name}
                      <small>
                        {o.items.reduce((n, i) => n + i.quantity_kg, 0)} kg
                      </small>
                    </td>
                    <td>TZS {money(o.total_tzs)}</td>
                    <td>
                      <Badge status={o.status} />
                    </td>
                  </tr>
                ))}
                {!orders.data?.length && (
                  <tr>
                    <td colSpan={4}>
                      Your orders will appear here once you start trading.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
        <section className="panel price-panel">
          <div className="section-heading">
            <div>
              <h2>Market pulse</h2>
              <p className="muted">Illustrative reference prices</p>
            </div>
            <TrendingUp size={20} />
          </div>
          {prices.data?.slice(0, 4).map((p) => (
            <div className="market-price-row" key={p.id}>
              <div className="crop-dot">
                <Leaf size={18} />
              </div>
              <div>
                <strong>{p.crop}</strong>
                <small>
                  <MapPin size={10} />
                  {p.region}
                </small>
              </div>
              <div>
                <strong>{money(p.price_tzs)}</strong>
                <small>TZS / kg</small>
              </div>
            </div>
          ))}
          <p className="fine-print">
            Demo prices, not live market data. Confirm prices directly with the
            farmer.
          </p>
        </section>
      </div>
      <div className="section-heading">
        <div>
          <h2>
            {user.role === "farmer" ? "From your farm" : "Fresh opportunities"}
          </h2>
          <p className="muted">Quality produce, ready for the next step</p>
        </div>
        <Link to="/marketplace" className="text-link">
          Browse all
          <ArrowRight size={15} />
        </Link>
      </div>
      <div className="produce-grid">
        {produce.data
          ?.filter((p) => p.active)
          .slice(0, 3)
          .map((p) => (
            <ProduceCard key={p.id} produce={p} />
          ))}
      </div>
    </>
  );
}
