import { redirect } from "next/navigation";

export default function Page() {
  // Route removed: Expired items now live under Inventory dialog > Expired tab.
  redirect("/");
}
