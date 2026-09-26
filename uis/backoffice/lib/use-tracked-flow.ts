"use client";

import { useEffect, useRef } from "react";
import { track } from "@/lib/telemetry";

type FlowName = "inbound_order" | "outbound_order" | "register" | "password_reset";

export function useTrackedFlow(flow: FlowName): () => void {
  const finished = useRef(false);

  useEffect(() => {
    track("flow_started", { flow });
    return () => {
      if (!finished.current) {
        track("flow_abandoned", { flow });
      }
    };
  }, [flow]);

  return () => {
    finished.current = true;
  };
}
