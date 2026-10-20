import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const nextConfig: NextConfig = {
  // Mantém a raiz de compilação independente do workspace DevFlow AI.
  turbopack: {
    root: fileURLToPath(new URL(".", import.meta.url)),
  },
  poweredByHeader: false,
};

export default nextConfig;
