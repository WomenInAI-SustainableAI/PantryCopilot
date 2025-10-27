import { differenceInDays, differenceInHours } from "date-fns";

export type ExpirySeverity = "expired" | "urgent" | "soon" | "normal";

export function getExpiryInfo(expiryIso: string): { text: string; severity: ExpirySeverity } {
  const now = new Date();
  const exp = new Date(expiryIso);
  const diffMs = exp.getTime() - now.getTime();
  if (isNaN(exp.getTime())) {
    return { text: "Invalid date", severity: "normal" };
  }
  if (diffMs < 0) return { text: "Expired", severity: "expired" };

  const hours = differenceInHours(exp, now);
  if (hours < 24) {
    const hoursDisplay = Math.max(1, hours);
    return { text: `Expires in ${hoursDisplay}h`, severity: "urgent" };
  }

  const days = differenceInDays(exp, now);
  const text = `Expires in ${days}d`;
  if (days <= 3) return { text, severity: "urgent" };
  if (days <= 7) return { text, severity: "soon" };
  return { text, severity: "normal" };
}
