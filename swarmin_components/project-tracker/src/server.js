const { createApp } = require('./app');

const port = Number(process.env.PORT || 3000);

createApp().listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Server listening on ${port}`);
});
