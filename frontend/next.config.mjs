/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Emit a minimal standalone server for the Docker image.
  output: "standalone",
};

export default nextConfig;
