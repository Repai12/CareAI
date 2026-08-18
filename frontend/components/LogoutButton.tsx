"use client";

import { useRouter } from "next/navigation";

export default function LogoutButton() {
  const router = useRouter();

  function handleLogout() {
    localStorage.removeItem("careai_token");
    localStorage.removeItem("careai_role");
    router.push("/login");
  }

  return (
    <button
      onClick={handleLogout}
      className="text-xs font-medium text-alert border border-alert/30 rounded-full px-3 py-1.5 hover:bg-alert/10 transition"
    >
      Log out
    </button>
  );
}
