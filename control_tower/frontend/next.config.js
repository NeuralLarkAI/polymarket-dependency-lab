const isGitHubPages = process.env.GITHUB_PAGES === 'true';

const nextConfig = {
  reactStrictMode: true,
  ...(isGitHubPages ? {
    output: 'export',
    basePath: '/polymarket-dependency-lab',
  } : {}),
  images: {
    unoptimized: true,
  },
};
module.exports = nextConfig;
