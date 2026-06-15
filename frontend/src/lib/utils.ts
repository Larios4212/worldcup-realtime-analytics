import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMinute(minute: number | null): string {
  if (minute === null) return "-";
  if (minute > 90) return `90+${minute - 90}'`;
  return `${minute}'`;
}

export function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("es-ES", {
    day: "numeric",
    month: "short",
  });
}
