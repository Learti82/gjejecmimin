import { productVisual } from "@/lib/productImage";
import type { Category } from "@/lib/types";

// A visual tile for a product, derived from its name + category (see
// lib/productImage). Gives users an at-a-glance sense of what a listing is
// without any stored image or external call.

export function ProductImage({
  name,
  category,
  size = "md",
}: {
  name: string;
  category: Category;
  size?: "sm" | "md" | "lg";
}) {
  const { emoji, bg } = productVisual(name, category);
  const dims =
    size === "lg"
      ? "h-20 w-20 text-4xl"
      : size === "sm"
        ? "h-10 w-10 text-xl"
        : "h-14 w-14 text-2xl";
  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-xl ${bg} ${dims}`}
      role="img"
      aria-label={name}
    >
      <span aria-hidden>{emoji}</span>
    </div>
  );
}
