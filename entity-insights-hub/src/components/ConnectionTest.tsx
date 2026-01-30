/**
 * Component to test backend connection
 * This can be added to Login page temporarily for debugging
 */

import { useEffect, useState } from "react";
import { testApi } from "@/lib/api";

export function ConnectionTest() {
  const [status, setStatus] = useState<"checking" | "connected" | "error">("checking");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await testApi.test();
        if (response.success) {
          setStatus("connected");
          setMessage("Backend connected successfully");
        } else {
          setStatus("error");
          setMessage("Backend responded but with error");
        }
      } catch (error: any) {
        setStatus("error");
        setMessage(error.message || "Cannot connect to backend");
      }
    };

    testConnection();
  }, []);

  if (status === "checking") {
    return (
      <div className="text-xs text-muted-foreground">
        Checking connection...
      </div>
    );
  }

  return (
    <div
      className={`text-xs p-2 rounded ${
        status === "connected"
          ? "bg-green-100 text-green-700"
          : "bg-red-100 text-red-700"
      }`}
    >
      {status === "connected" ? "✅ " : "❌ "}
      {message}
    </div>
  );
}

