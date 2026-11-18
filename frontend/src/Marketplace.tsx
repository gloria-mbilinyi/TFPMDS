import { useState, type FormEvent } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import {
  ErrorBox,
  Loading,
  Empty,
  PageTitle,
  ProduceCard,
  useData,
} from "./components";
import type { Produce } from "./types";
import { regions } from "./AuthPages";

export function Marketplace() {
  const [query, setQuery] = useState("");
  const { data, error, loading } = useData<Produce[]>("/produce" + query);
  function search(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const params = new URLSearchParams();
    new FormData(e.currentTarget).forEach((v, k) => {
      if (v) params.set(k, String(v));
    });
    setQuery("?" + params.toString());
  }
  return (
    <>
      <PageTitle
        eyebrow="FRESH FROM THE FARM"
        title="The marketplace"
        description="Discover quality produce from verified farmers across Tanzania."
      />
      <form onSubmit={search} className="market-filter panel">
        <div className="search-field">
          <Search size={18} />
          <input
            name="q"
            aria-label="Search produce"
            placeholder="Search rice, beans, tomatoes…"
          />
        </div>
        <div className="filter-grid">
          <label>
            Crop
            <select name="crop">
              <option value="">All crops</option>
              {[
                "Rice",
                "Maize",
                "Beans",
                "Potatoes",
                "Tomatoes",
                "Avocado",
                "Sunflower",
              ].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            Region
            <select name="region">
              <option value="">All regions</option>
              {regions.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </label>
          <label>
            Min. price (TZS/kg)
            <input name="min_price" type="number" min={0} placeholder="Any" />
          </label>
          <label>
            Max. price (TZS/kg)
            <input name="max_price" type="number" min={1} placeholder="Any" />
          </label>
          <label>
            Min. quantity (kg)
            <input
              name="min_quantity"
              type="number"
              min={0}
              placeholder="Any"
            />
          </label>
          <button className="btn primary">
            <SlidersHorizontal size={16} />
            Apply filters
          </button>
        </div>
      </form>
      <ErrorBox message={error} />
      {loading ? (
        <Loading />
      ) : (
        <>
          <div className="section-heading">
            <h2>
              Available produce{" "}
              <span className="count">{data?.length || 0}</span>
            </h2>
            <span className="muted">Prices in Tanzanian shillings per kg</span>
          </div>
          {data?.length ? (
            <div className="produce-grid">
              {data.map((p) => (
                <ProduceCard key={p.id} produce={p} />
              ))}
            </div>
          ) : (
            <Empty>
              No produce matches your filters. Try another crop or region.
            </Empty>
          )}
        </>
      )}
    </>
  );
}
