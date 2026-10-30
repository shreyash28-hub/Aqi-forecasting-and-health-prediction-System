"use client";

import { useState } from "react";
import { ExternalLink, Globe, LocateFixed, MapPin, Navigation, Phone, Search, Siren } from "lucide-react";
import { ErrorState, Panel, PanelTitle } from "@/components/common";
import { Skeleton } from "@/components/ui/skeleton";
import { useAsync } from "@/hooks/use-async";
import { api, type Hospital } from "@/lib/api";
import { cn } from "@/lib/utils";
import { HospitalMap } from "./hospital-map";

const RADII = [3, 5, 10];
const telHref = (p: string) => `tel:${p.replace(/[^\d+]/g, "")}`;
const directions = (h: Hospital) => `https://www.google.com/maps/dir/?api=1&destination=${h.lat},${h.lon}`;
/** Google Maps search for the place; its listing usually shows the phone number. */
const lookUp = (h: Hospital, city: string) =>
  `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${h.name}, ${h.address ?? city}`)}`;

type Origin = { kind: "city" } | { kind: "me"; lat: number; lon: number };

/**
 * Nearby hospitals with contact details, on a map and in a list. Enquiry only: the
 * site shows how to contact a hospital and never books anything.
 */
export function HospitalsPanel({ city, className, id }: { city: string; className?: string; id?: string }) {
  const [radius, setRadius] = useState(5);
  const [origin, setOrigin] = useState<Origin>({ kind: "city" });
  const [locating, setLocating] = useState(false);
  const [geoError, setGeoError] = useState<string>();
  const [selected, setSelected] = useState<string>();
  const [phoneOnly, setPhoneOnly] = useState(false);

  const query = origin.kind === "me" ? { lat: origin.lat, lon: origin.lon, radiusKm: radius } : { city, radiusKm: radius };
  const res = useAsync((signal) => api.hospitals(query, signal), [city, radius, origin]);
  const list = (res.data?.hospitals ?? []).filter((h) => !phoneOnly || h.phones.length > 0);
  const withPhone = (res.data?.hospitals ?? []).filter((h) => h.phones.length > 0).length;
  const where = origin.kind === "me" ? "your location" : `${city} city centre`;

  function useMyLocation() {
    if (!("geolocation" in navigator)) return setGeoError("Your browser can't share its location.");
    setLocating(true);
    setGeoError(undefined);
    navigator.geolocation.getCurrentPosition(
      // Rounded to about 100 m before it leaves the browser; it is not stored.
      (p) => { setOrigin({ kind: "me", lat: +p.coords.latitude.toFixed(3), lon: +p.coords.longitude.toFixed(3) }); setLocating(false); setSelected(undefined); },
      () => { setGeoError("Location was not shared, so the city centre is used."); setLocating(false); },
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 },
    );
  }

  return (
    <Panel id={id} className={cn("scroll-mt-20", className)}>
      <PanelTitle
        sub={res.data ? `${res.data.hospitals.length} within ${radius} km of ${where}` : `within ${radius} km of ${where}`}
        action={
          <div className="flex flex-wrap items-center gap-2">
            <div role="radiogroup" aria-label="Search radius" className="inline-flex overflow-hidden rounded-[7px] border border-border-strong bg-card">
              {RADII.map((r) => (
                <button key={r} role="radio" aria-checked={radius === r} onClick={() => { setRadius(r); setSelected(undefined); }}
                  className={cn("px-3 py-1.5 text-[13px] font-medium", radius === r ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground")}>
                  {r} km
                </button>
              ))}
            </div>
            {origin.kind === "me" ? (
              <button onClick={() => { setOrigin({ kind: "city" }); setSelected(undefined); }}
                className="flex h-8 items-center gap-1.5 rounded-[7px] border border-border-strong px-3 text-[13px] font-medium hover:bg-muted">
                <MapPin className="size-3.5" aria-hidden />Use {city} centre
              </button>
            ) : (
              <button onClick={useMyLocation} disabled={locating}
                className="flex h-8 items-center gap-1.5 rounded-[7px] border border-border-strong px-3 text-[13px] font-medium hover:bg-muted disabled:opacity-60">
                <LocateFixed className="size-3.5" aria-hidden />{locating ? "Locating…" : "Use my location"}
              </button>
            )}
          </div>
        }
      >
        Nearby hospitals
      </PanelTitle>
      {geoError && <p className="mt-2 text-[12.5px] text-muted-foreground">{geoError}</p>}

      {res.error ? <ErrorState className="mt-4" message={res.error.message} onRetry={res.retry} /> : (
        <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_400px] wide:grid-cols-[minmax(0,1fr)_460px]">
          <div className="relative self-start overflow-hidden rounded-[8px] border">
            {res.data && (
              <HospitalMap centre={res.data.centre} radiusKm={res.data.radius_km} hospitals={list} selectedId={selected}
                onSelect={setSelected} centreLabel={where} className="h-[340px] w-full lg:h-[520px]" />
            )}
            {res.loading && (
              <div className="absolute inset-0 z-[500] grid place-items-center bg-card/70 text-center text-sm text-muted-foreground" aria-busy="true">
                <span>Looking up hospitals…<br /><span className="text-[12.5px] text-faint">The first search for an area can take up to 30 seconds.</span></span>
              </div>
            )}
            {!res.data && <Skeleton className="h-[340px] w-full lg:h-[520px]" />}
          </div>

          <div className="flex min-h-0 flex-col">
            {res.data && res.data.hospitals.length > 0 && (
              <p className="mb-2 text-[12.5px] text-muted-foreground">
                <b className="num font-medium text-foreground">{withPhone}</b> of <b className="num font-medium text-foreground">{res.data.hospitals.length}</b> have a phone number listed.
                {withPhone < res.data.hospitals.length && <> For the others, use &ldquo;Find phone number&rdquo;.</>}
              </p>
            )}
            <label className="mb-2 flex items-center gap-2 text-[13px] text-muted-foreground">
              <input type="checkbox" checked={phoneOnly} onChange={(e) => setPhoneOnly(e.target.checked)} className="size-4 accent-[var(--brand)]" />
              Only show hospitals with a phone number
            </label>
            {!res.data ? <Skeleton className="h-[480px]" /> : list.length === 0 ? (
              <p className="rounded-[8px] border border-dashed p-5 text-sm text-muted-foreground">
                No hospitals found within {radius} km{phoneOnly ? " with a phone number" : ""}. Try a larger radius.
              </p>
            ) : (
              <ul className="max-h-[480px] space-y-2 overflow-y-auto pr-1" aria-label="Hospitals, nearest first">
                {list.map((h) => <HospitalItem key={h.id} h={h} city={city} selected={h.id === selected} onSelect={() => setSelected(h.id)} />)}
              </ul>
            )}
          </div>
        </div>
      )}

      <div className="mt-4 flex flex-col gap-1.5 border-t pt-3 text-[12.5px] text-faint">
        <p className="flex items-center gap-2 font-medium text-muted-foreground">
          <Siren className="size-4 shrink-0 text-[#d9453f]" aria-hidden />
          In an emergency, call 112 (or 108 for an ambulance) instead of using this list.
        </p>
        <p>Contact details only: Airware does not book appointments. Listings come from OpenStreetMap contributors and may be incomplete or out of date, so call ahead.</p>
      </div>
    </Panel>
  );
}

function HospitalItem({ h, city, selected, onSelect }: { h: Hospital; city: string; selected: boolean; onSelect: () => void }) {
  return (
    <li>
      <div
        onClick={onSelect}
        className={cn("cursor-pointer rounded-[8px] border p-3 transition-colors hover:bg-muted",
          selected && "border-brand shadow-[inset_0_0_0_1px_var(--brand)]")}
        aria-current={selected || undefined}
      >
        <div className="flex items-start justify-between gap-3">
          <button type="button" onClick={onSelect} className="text-left text-sm font-medium leading-snug hover:underline">{h.name}</button>
          <span className="num shrink-0 text-[12.5px] text-muted-foreground">{h.distance_km.toFixed(1)} km</span>
        </div>
        {h.emergency && (
          <span className="mt-1 inline-flex items-center gap-1 rounded-[5px] bg-[#d9453f]/12 px-1.5 py-0.5 text-[11.5px] font-medium text-[color-mix(in_srgb,#d9453f_75%,var(--foreground))]">
            <Siren className="size-3" aria-hidden />Emergency department
          </span>
        )}
        {h.address && <p className="mt-1 text-[12.5px] text-muted-foreground">{h.address}</p>}
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1.5 text-[13px]" onClick={(e) => e.stopPropagation()}>
          {h.phones.length > 0 ? h.phones.slice(0, 2).map((p) => (
            <a key={p} href={telHref(p)} className="flex items-center gap-1.5 font-medium text-brand-ink hover:underline">
              <Phone className="size-3.5" aria-hidden /><span className="num">{p}</span>
            </a>
          )) : (
            <a href={lookUp(h, city)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 font-medium text-brand-ink hover:underline"
              title="Opens Google Maps, which usually lists the phone number">
              <Search className="size-3.5" aria-hidden />Find phone number
            </a>
          )}
          {h.website && (
            <a href={h.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground">
              <Globe className="size-3.5" aria-hidden />Website
            </a>
          )}
          <a href={directions(h)} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground">
            <Navigation className="size-3.5" aria-hidden />Directions
          </a>
          <a href={h.osm_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground">
            <ExternalLink className="size-3.5" aria-hidden />Map entry
          </a>
        </div>
      </div>
    </li>
  );
}
