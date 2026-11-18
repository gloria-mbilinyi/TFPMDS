import { useState, type FormEvent } from "react";
import {
  BarChart3,
  Download,
  Plus,
  ShieldCheck,
  Users,
  Wallet,
} from "lucide-react";
import { api, date, human, money, patch, post } from "./api";
import {
  Badge,
  Empty,
  ErrorBox,
  Loading,
  Metric,
  PageTitle,
  Success,
  useData,
} from "./components";
import { useSession } from "./session";
import type { MarketPrice, Notice, Report, User } from "./types";
import { regions } from "./AuthPages";

export function Admin() {
  const { user } = useSession();
  const users = useData<User[]>("/admin/users");
  const [error, setError] = useState(""),
    [success, setSuccess] = useState(""),
    [busy, setBusy] = useState(false),
    [filter, setFilter] = useState("pending"),
    [staffForm, setStaffForm] = useState(false);
  async function action(path: string, body: unknown, method = "POST") {
    setBusy(true);
    setError("");
    try {
      if (method === "PATCH") await patch(path, body);
      else await post(path, body);
      setSuccess("Account updated.");
      await users.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function staff(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    setBusy(true);
    setError("");
    try {
      await post("/admin/staff", Object.fromEntries(new FormData(form)));
      setSuccess("Staff account created.");
      setStaffForm(false);
      await users.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (user?.role !== "administrator")
    return <ErrorBox message="Administrator access is required." />;
  return (
    <>
      <PageTitle
        eyebrow="SYSTEM ADMINISTRATION"
        title="People & approvals"
        description="Review farm and buyer profiles, manage account access and create logistics staff."
        actions={
          <button
            className="btn primary"
            onClick={() => setStaffForm(!staffForm)}
          >
            <Plus size={15} />
            Add staff
          </button>
        }
      />
      <ErrorBox message={error || users.error} />
      {success && <Success>{success}</Success>}
      <div className="metrics">
        <Metric
          label="Registered accounts"
          value={users.data?.length || 0}
          note="All roles"
          icon={<Users />}
        />
        <Metric
          label="Awaiting review"
          value={users.data?.filter((u) => u.status === "pending").length || 0}
          note="Farmer and buyer registrations"
          icon={<ShieldCheck />}
        />
        <Metric
          label="Verified farmers"
          value={
            users.data?.filter(
              (u) => u.role === "farmer" && u.status === "approved",
            ).length || 0
          }
          note="Approved farming accounts"
          icon={<Users />}
        />
        <Metric
          label="Approved buyers"
          value={
            users.data?.filter(
              (u) => u.role === "buyer" && u.status === "approved",
            ).length || 0
          }
          note="Approved buying accounts"
          icon={<Users />}
        />
      </div>
      {staffForm && (
        <section className="panel narrow" style={{ marginBottom: 22 }}>
          <h2>Create a staff account</h2>
          <form onSubmit={staff}>
            <div className="form-grid mt">
              <label>
                Full name
                <input name="name" required minLength={2} maxLength={100} />
              </label>
              <label>
                Role
                <select name="role">
                  <option value="logistics">Logistics officer</option>
                  <option value="transporter">Transporter</option>
                </select>
              </label>
              <label>
                Email address
                <input type="email" name="email" required />
              </label>
              <label>
                Initial password
                <input
                  type="password"
                  name="password"
                  required
                  minLength={10}
                  maxLength={128}
                  autoComplete="new-password"
                />
              </label>
              <label>
                Phone
                <input
                  name="phone"
                  required
                  pattern="\+255[67][0-9]{8}"
                  placeholder="+255712345678"
                />
              </label>
              <label>
                Region
                <select name="region">
                  {regions.map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="form-actions">
              <button className="btn primary" disabled={busy}>
                Create staff
              </button>
              <button
                type="button"
                className="btn outline"
                onClick={() => setStaffForm(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </section>
      )}
      <div className="tabs" role="group" aria-label="Filter accounts">
        {["pending", "approved", "rejected", "all"].map((v) => (
          <button
            className={filter === v ? "selected" : ""}
            onClick={() => setFilter(v)}
            key={v}
          >
            {human(v)}
          </button>
        ))}
      </div>
      {users.loading ? (
        <Loading />
      ) : (
        <div className="stack">
          {users.data
            ?.filter((u) => filter === "all" || u.status === filter)
            .map((u) => (
              <section className="panel" key={u.id}>
                <div className="section-heading">
                  <div>
                    <h2>{u.name}</h2>
                    <p className="muted">
                      {human(u.role)} · {u.email} · {u.phone}
                    </p>
                  </div>
                  <div className="row">
                    <Badge status={u.status} />
                    {!u.active && <Badge status="inactive" />}
                  </div>
                </div>
                <div className="account-facts">
                  <span>
                    <small>REGION / LOCATION</small>
                    {u.region} · {u.location || "Not provided"}
                  </span>
                  {u.role === "farmer" ? (
                    <>
                      <span>
                        <small>FARM SIZE</small>
                        {u.farm_size_acres} acres
                      </span>
                      <span>
                        <small>CROP CATEGORIES</small>
                        {u.crop_categories || "Not provided"}
                      </span>
                    </>
                  ) : (
                    <span>
                      <small>BUSINESS</small>
                      {u.business_name || "Not provided"}
                    </span>
                  )}
                </div>
                {u.verification_note && (
                  <p className="fine-print">
                    Review note: {u.verification_note}
                  </p>
                )}
                <div className="order-actions">
                  {["farmer", "buyer"].includes(u.role) && (
                    <form
                      className="approval-form"
                      onSubmit={(e) => {
                        e.preventDefault();
                        const values = new FormData(e.currentTarget);
                        action(
                          `/admin/users/${u.id}/approval`,
                          Object.fromEntries(values),
                        );
                      }}
                    >
                      <label>
                        Review decision
                        <select
                          name="status"
                          defaultValue={
                            u.status === "approved" ? "rejected" : "approved"
                          }
                        >
                          <option value="approved">Approve</option>
                          <option value="rejected">Reject</option>
                        </select>
                      </label>
                      <label>
                        Verification note
                        <input
                          name="note"
                          required
                          minLength={3}
                          maxLength={300}
                          placeholder="Document your review decision"
                        />
                      </label>
                      <button className="btn primary small" disabled={busy}>
                        Save review
                      </button>
                    </form>
                  )}
                  {u.id !== user.id && (
                    <button
                      disabled={busy}
                      className="btn small outline"
                      onClick={() =>
                        action(
                          `/admin/users/${u.id}/active`,
                          { active: !u.active },
                          "PATCH",
                        )
                      }
                    >
                      {u.active ? "Deactivate account" : "Activate account"}
                    </button>
                  )}
                </div>
              </section>
            ))}
          {!users.data?.some(
            (u) => filter === "all" || u.status === filter,
          ) && (
            <Empty>No {filter === "all" ? "" : filter} accounts to show.</Empty>
          )}
        </div>
      )}
    </>
  );
}

export function MarketPrices() {
  const { user } = useSession();
  const prices = useData<MarketPrice[]>("/market-prices");
  const [editing, setEditing] = useState<MarketPrice | null>(null),
    [show, setShow] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [saved, setSaved] = useState("");
  const admin = user?.role === "administrator";
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const raw = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await post("/admin/market-prices", {
        ...raw,
        price_tzs: Number(raw.price_tzs),
      });
      setSaved("Reference price saved.");
      setShow(false);
      await prices.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function remove(id: number) {
    setBusy(true);
    setError("");
    try {
      await api("/admin/market-prices/" + id, { method: "DELETE" });
      setSaved("Reference price removed.");
      await prices.reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="MARKET INFORMATION"
        title="Market reference prices"
        description="Illustrative prices per kilogram. Check the observation date and source before comparing."
        actions={
          admin && (
            <button
              className="btn primary"
              onClick={() => {
                setEditing(null);
                setShow(true);
              }}
            >
              <Plus size={15} />
              Add reference price
            </button>
          )
        }
      />
      <ErrorBox message={error || prices.error} />
      {saved && <Success>{saved}</Success>}
      {admin && show && (
        <section className="panel narrow" style={{ marginBottom: 22 }}>
          <h2>{editing ? "Update reference price" : "Add reference price"}</h2>
          <form onSubmit={save} key={editing?.id || "new"}>
            <div className="form-grid mt">
              <label>
                Crop
                <input
                  name="crop"
                  defaultValue={editing?.crop}
                  required
                  minLength={2}
                  maxLength={50}
                  readOnly={!!editing}
                />
              </label>
              <label>
                Region
                <input
                  name="region"
                  defaultValue={editing?.region}
                  required
                  minLength={2}
                  maxLength={60}
                  readOnly={!!editing}
                />
              </label>
              <label>
                Price (TZS/kg)
                <input
                  name="price_tzs"
                  type="number"
                  min={1}
                  max={1000000000}
                  required
                  defaultValue={editing?.price_tzs}
                />
              </label>
              <label>
                Observation date
                <input
                  name="observed_on"
                  type="date"
                  required
                  defaultValue={
                    editing?.observed_on ||
                    new Date().toISOString().slice(0, 10)
                  }
                />
              </label>
              <label className="wide">
                Source
                <input
                  name="source"
                  required
                  minLength={3}
                  maxLength={100}
                  defaultValue={editing?.source || "Illustrative academic demo"}
                />
              </label>
            </div>
            <div className="form-actions">
              <button className="btn primary" disabled={busy}>
                Save price
              </button>
              <button
                className="btn outline"
                type="button"
                onClick={() => setShow(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </section>
      )}
      {prices.loading ? (
        <Loading />
      ) : (
        <section className="panel table-wrap">
          <table>
            <thead>
              <tr>
                <th>Crop</th>
                <th>Region</th>
                <th>Reference / kg</th>
                <th>Observed</th>
                <th>Source</th>
                {admin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {prices.data?.map((p) => (
                <tr key={p.id}>
                  <td>
                    <strong>{p.crop}</strong>
                  </td>
                  <td>{p.region}</td>
                  <td>TZS {money(p.price_tzs)}</td>
                  <td>{date(p.observed_on)}</td>
                  <td>{p.source}</td>
                  {admin && (
                    <td>
                      <div className="row">
                        <button
                          className="btn outline small"
                          disabled={busy}
                          onClick={() => {
                            setEditing(p);
                            setShow(true);
                          }}
                        >
                          Edit
                        </button>
                        <button
                          className="btn danger small"
                          disabled={busy}
                          onClick={() => remove(p.id)}
                        >
                          Remove
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          {!prices.data?.length && (
            <Empty>No reference prices have been added.</Empty>
          )}
        </section>
      )}
    </>
  );
}

export function csvCell(value: unknown) {
  const text = String(value);
  return (
    '"' + (/^[=+\-@]/.test(text) ? "'" : "") + text.replaceAll('"', '""') + '"'
  );
}
function exportReport(report: Report) {
  const rows = [
    ["TFPMDS simulated sales report"],
    ["Metric", "Value"],
    ...Object.entries(report)
      .filter(([, v]) => typeof v === "number")
      .map(([k, v]) => [human(k), v]),
    [],
    ["Produce", "Quantity (kg)", "Sales (TZS)"],
    ...report.sales_by_produce.map((r) => [
      r.produce,
      r.quantity_kg,
      r.sales_tzs,
    ]),
    [],
    ["Definition", report.definition],
  ];
  const blob = new Blob(
    [rows.map((row) => row.map(csvCell).join(",")).join("\r\n")],
    { type: "text/csv;charset=utf-8" },
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "TFPMDS-simulated-sales.csv";
  a.click();
  URL.revokeObjectURL(url);
}
function Bars({ rows }: { rows: { label: string; value: number }[] }) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <div className="bar-chart">
      {rows.length ? (
        rows.map((r) => (
          <div className="bar-item" key={r.label}>
            <div className="row">
              <span>{r.label}</span>
              <strong>{money(r.value)}</strong>
            </div>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: (100 * r.value) / max + "%" }}
              />
            </div>
          </div>
        ))
      ) : (
        <Empty>No successful simulated sales yet.</Empty>
      )}
    </div>
  );
}
export function Reports() {
  const { user } = useSession();
  const { data, error, loading } = useData<Report>("/reports/summary");
  if (user?.role !== "administrator")
    return <ErrorBox message="Administrator access is required." />;
  return (
    <>
      <PageTitle
        eyebrow="SYSTEM PERFORMANCE"
        title="Reports & analytics"
        description="A clear view of marketplace activity and simulated gross sales."
        actions={
          <button
            className="btn outline"
            disabled={!data}
            onClick={() => data && exportReport(data)}
          >
            <Download size={16} />
            Export CSV
          </button>
        }
      />
      <ErrorBox message={error} />
      {loading ? (
        <Loading />
      ) : (
        data && (
          <>
            <div className="metrics">
              <Metric
                label="Gross simulated sales"
                value={"TZS " + money(data.gross_sales_tzs)}
                note="Successful simulations only"
                icon={<Wallet />}
              />
              <Metric
                label="Purchase orders"
                value={data.orders}
                note={`${data.completed_orders} completed`}
                icon={<BarChart3 />}
              />
              <Metric
                label="Registered users"
                value={data.users}
                note={`${data.pending_approvals} awaiting approval`}
                icon={<Users />}
              />
              <Metric
                label="Simulated SMS"
                value={data.sms_simulated}
                note="Durable notification records"
                icon={<ShieldCheck />}
              />
            </div>
            <div className="data-grid">
              <section className="panel">
                <h2>Sales by produce</h2>
                <p className="muted">Gross simulated value in TZS</p>
                <Bars
                  rows={data.sales_by_produce.map((r) => ({
                    label: r.produce,
                    value: r.sales_tzs,
                  }))}
                />
              </section>
              <section className="panel">
                <h2>Sales by farmer region</h2>
                <p className="muted">Gross simulated value in TZS</p>
                <Bars
                  rows={data.sales_by_region.map((r) => ({
                    label: r.region,
                    value: r.sales_tzs,
                  }))}
                />
              </section>
              <section className="panel">
                <h2>Order lifecycle</h2>
                <Bars
                  rows={data.orders_by_status.map((r) => ({
                    label: human(r.status),
                    value: r.count,
                  }))}
                />
              </section>
              <section className="panel">
                <h2>Reporting definitions</h2>
                <p className="detail-description">{data.definition}</p>
                <p className="detail-description">
                  Active listings: {data.active_listings}. Shipments:{" "}
                  {data.shipments}. Currently delivered shipments:{" "}
                  {data.delivered_shipments}. Farmers: {data.farmers}. Buyers:{" "}
                  {data.buyers}.
                </p>
              </section>
            </div>
          </>
        )
      )}
    </>
  );
}

export function SmsLog() {
  const { data, error, loading } = useData<Notice[]>("/admin/sms-log");
  return (
    <>
      <PageTitle
        title="SMS simulation log"
        description="Local provider records. No messages are sent to a mobile network."
      />
      <ErrorBox message={error} />
      {loading ? (
        <Loading />
      ) : (
        <section className="panel table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Recipient</th>
                <th>Type</th>
                <th>Message</th>
                <th>Reference</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((n) => (
                <tr key={n.id}>
                  <td>{date(n.created_at)}</td>
                  <td>{n.recipient}</td>
                  <td>{human(n.kind)}</td>
                  <td className="message-cell">{n.message}</td>
                  <td>
                    <small>{n.sms_reference}</small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </>
  );
}
