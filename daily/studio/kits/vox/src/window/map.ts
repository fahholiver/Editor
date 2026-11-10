import { geoCentroid, geoMercator, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import world from "world-atlas/countries-50m.json";

// Natural Earth 1:50m countries (world-atlas), Mercator centred on central Italy.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const topo = world as any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fc = feature(topo, topo.objects.countries) as any;

export const proj = geoMercator().center([12.3, 41.9]).scale(6500).translate([540, 760]);
const path = geoPath(proj);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const LAND: { d: string; italy: boolean }[] = fc.features
  .filter((f: any) => {
    const [lon, lat] = geoCentroid(f);
    return lon > -15 && lon < 45 && lat > 25 && lat < 62;
  })
  .map((f: any) => ({ d: path(f) || "", italy: f.properties?.name === "Italy" }));

export const P = (lon: number, lat: number) => proj([lon, lat]) as [number, number];
