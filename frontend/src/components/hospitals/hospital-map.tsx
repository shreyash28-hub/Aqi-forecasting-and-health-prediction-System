"use client";

import { useEffect, useRef } from "react";
import type * as Leaflet from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Hospital } from "@/lib/api";

type L = typeof Leaflet;

const pin = (L: L, h: Hospital, selected: boolean) =>
  L.divIcon({
    className: "",
    html: `<span class="hm-pin${selected ? " is-selected" : ""}${h.emergency ? " is-er" : ""}"></span>`,
    iconSize: [22, 22],
    iconAnchor: [11, 22],
    tooltipAnchor: [0, -20],
  });

/**
 * OpenStreetMap map with one pin per hospital and the search radius. Clicking a pin
 * selects it; selecting from the list pans to it.
 */
export function HospitalMap({ centre, radiusKm, hospitals, selectedId, onSelect, centreLabel, className }: {
  centre: { lat: number; lon: number };
  radiusKm: number;
  hospitals: Hospital[];
  selectedId?: string;
  onSelect: (id: string) => void;
  centreLabel: string;
  className?: string;
}) {
  const el = useRef<HTMLDivElement>(null);
  const lib = useRef<L | null>(null);
  const map = useRef<Leaflet.Map | null>(null);
  const layer = useRef<Leaflet.LayerGroup | null>(null);
  const markers = useRef(new Map<string, Leaflet.Marker>());
  const select = useRef(onSelect);

  useEffect(() => { select.current = onSelect; }, [onSelect]);

  // Create the map once (Leaflet touches `window`, so it is imported here, not at the top).
  useEffect(() => {
    let cancelled = false;
    import("leaflet").then((mod) => {
      if (cancelled || !el.current || map.current) return;
      const L = (mod.default ?? mod) as L;
      lib.current = L;
      map.current = L.map(el.current, { zoomControl: true, scrollWheelZoom: false });
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map.current);
      layer.current = L.layerGroup().addTo(map.current);
      map.current.on("focus", () => map.current?.scrollWheelZoom.enable());
      map.current.on("blur", () => map.current?.scrollWheelZoom.disable());
      draw();
    });
    return () => {
      cancelled = true;
      map.current?.remove();
      map.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function draw() {
    const L = lib.current, m = map.current, g = layer.current;
    if (!L || !m || !g) return;
    g.clearLayers();
    markers.current.clear();
    // Set the view first: Leaflet only attaches layers once the map has one.
    m.fitBounds(L.latLng(centre.lat, centre.lon).toBounds(radiusKm * 2000), { padding: [12, 12] });
    L.circle([centre.lat, centre.lon], {
      radius: radiusKm * 1000, className: "hm-ring", weight: 1.5, dashArray: "5 6", fillOpacity: 0.04,
    }).addTo(g);
    L.circleMarker([centre.lat, centre.lon], { radius: 6, color: "#ffffff", weight: 2, fillColor: "#0b6e74", fillOpacity: 1 })
      .bindTooltip(centreLabel).addTo(g);
    for (const h of hospitals) {
      const mk = L.marker([h.lat, h.lon], { icon: pin(L, h, h.id === selectedId), title: h.name, riseOnHover: true })
        .bindTooltip(`${h.name} · ${h.distance_km.toFixed(1)} km`)
        .on("click", () => select.current(h.id))
        .addTo(g);
      markers.current.set(h.id, mk);
    }
  }

  // Redraw when the search or the results change.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { draw(); }, [centre.lat, centre.lon, radiusKm, hospitals, centreLabel]);

  // Highlight the selected hospital and bring it into view.
  useEffect(() => {
    const L = lib.current;
    if (!L) return;
    for (const h of hospitals) markers.current.get(h.id)?.setIcon(pin(L, h, h.id === selectedId));
    const mk = selectedId ? markers.current.get(selectedId) : undefined;
    if (mk && map.current) {
      mk.setZIndexOffset(1000);
      map.current.panTo(mk.getLatLng(), { animate: true });
    }
  }, [selectedId, hospitals]);

  return <div ref={el} className={className} role="region" aria-label="Map of nearby hospitals" />;
}
