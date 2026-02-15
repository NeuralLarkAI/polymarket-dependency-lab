const nextConfig = {
  reactStrictMode: true,
  output: 'export',  // Enable static export for GitHub Pages
  basePath: '/polymarket-dependency-lab',  // Match your repo name
  images: {
    unoptimized: true,  // Required for static export
  },
};
module.exports = nextConfig;
