module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Custom webpack configuration can be added here
      return webpackConfig;
    },
  },
  jest: {
    configure: (jestConfig) => {
      // Custom jest configuration can be added here
      return jestConfig;
    },
  },
};
