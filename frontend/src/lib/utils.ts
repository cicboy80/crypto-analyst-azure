import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null) return "N/A";
  if (Math.abs(value) >= 1e12) return `${(value / 1e12).toFixed(2)}T`;
  if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (Math.abs(value) >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

export function formatPrice(
  value: number | null | undefined,
  currency: string = "usd"
): string {
  if (value == null) return "N/A";
  const symbol =
    currency === "usd" ? "$" : currency === "eur" ? "\u20ac" : "\u00a3";
  if (Math.abs(value) >= 1e3) {
    return `${symbol}${formatNumber(value)}`;
  }
  return `${symbol}${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}
