import { MenusBrowser } from "@/components/MenusBrowser";
import { PageShell } from "@/components/PageShell";

// Menus & Nutrition. `?location=<id>` opens that location's menu on arrival
// (the What's Open Now page links here).
export default async function MenusPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const raw = Array.isArray(params.location)
    ? params.location[0]
    : params.location;
  const initialLocationId = raw && /^\d+$/.test(raw) ? Number(raw) : null;

  return (
    <PageShell
      title="Menus & Nutrition"
      lede="Menus, allergens, diets and nutrition for every dining location."
    >
      <MenusBrowser initialLocationId={initialLocationId} />
    </PageShell>
  );
}
