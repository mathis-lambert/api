///////////////////////////////////////////////////////////
//  Import modules
///////////////////////////////////////////////////////////
const path = require("path");
const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const mongoose = require("mongoose");
const favicon = require("serve-favicon");
require("dotenv").config({ path: path.resolve(__dirname, ".env") });

///////////////////////////////////////////////////////////
//  Configure and connect to MongoDB database
///////////////////////////////////////////////////////////
mongoose.set("strictQuery", false);
mongoose.Promise = global.Promise;
mongoose
  .connect(process.env.MONGO_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
  })
  .catch(({ message }) => {
    console.error(`Unable to connect to the mongodb instance: ${message}`);
  });

const db = mongoose.connection;
db.on("error", ({ message }) => {
  console.error(`Mongoose default connection error: ${message}`);
});
db.once("open", () => {
  console.info(`Mongoose default connection open to ${process.env.MONGO_URI}`);
});

///////////////////////////////////////////////////////////
//  Initialize Express and configure Middleware
///////////////////////////////////////////////////////////
const app = express();
app.set("port", process.env.APP_PORT || 8081);

// Serve static files
app.use(express.static(path.join(__dirname, "public")));
app.use(favicon(path.resolve(__dirname, "public", "images", "favicon.png")));

// Body parsing - parse application/x-www-form-urlencoded
app.use(bodyParser.urlencoded({ extended: false }));

// Body parsing - parse json
app.use(bodyParser.json());

// Handle cross-site request
app.use(cors());

///////////////////////////////////////////////////////////
//  Configure Routes
///////////////////////////////////////////////////////////
const routes = require("./routes")(app);

///////////////////////////////////////////////////////////
//  Start the server
///////////////////////////////////////////////////////////
const server = app.listen(app.get("port"), () => {
  console.log(`Express server listening on port ${server.address().port}`);
});
