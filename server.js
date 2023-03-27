///////////////////////////////////////////////////////////
//  Import modules
///////////////////////////////////////////////////////////
const path = require("path");
const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const mongoose = require("mongoose");
const morgan = require("morgan");
const fs = require("fs");
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

// Emplacement du fichier journal
const logFilePath = path.join(__dirname, "access.log");

// Créer un flux d'écriture pour le fichier journal
const accessLogStream = fs.createWriteStream(logFilePath, { flags: "a" });

// Configuration de morgan pour récupérer l'adresse IP à partir des en-têtes X-Forwarded-For ou X-Real-IP si elles sont disponibles
morgan.token("remote-addr", (req) => {
  const forwardedFor = req.headers["x-forwarded-for"];
  if (forwardedFor) {
    return forwardedFor.split(",")[0];
  }
  const realIp = req.headers["x-real-ip"];
  if (realIp) {
    return realIp;
  }
  return req.ip;
});

// Configuration de morgan
app.use(
  morgan(
    ':remote-addr - :remote-user [:date[clf]] ":method :url HTTP/:http-version" :status :res[content-length] ":referrer" ":user-agent"',
    { stream: accessLogStream }
  )
);

// Liste des adresses IP à bloquer
const blockedIPs = ["45.88.67.94", "45.139.105.222"];

// Middleware pour bloquer les requêtes provenant des adresses IP spécifiées
app.use((req, res, next) => {
  const clientIP = req.ip; // Adresse IP du client qui effectue la demande
  if (blockedIPs.includes(clientIP)) {
    res.status(403).send("Accès interdit");
  } else {
    next();
  }
});

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
