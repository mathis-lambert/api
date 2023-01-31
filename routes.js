const path = require("path");
const root = path.resolve(__dirname, ".");
const public = path.join(root, "public");
const dns = require("node:dns");
const validUrl = require("valid-url");
const shortId = require("shortid");

const urlSchema = require("./schemas");

module.exports = (app) => {
  ///////////////////////////////////////////////////////////
  // Testing/Debug Middleware
  ///////////////////////////////////////////////////////////
  //   app.use((req, res, next) => {
  //     console.debug(`DEBUG originalUrl: ${req.originalUrl}`);
  //     next();
  //   });

  ///////////////////////////////////////////////////////////
  // API Routes
  ///////////////////////////////////////////////////////////
  app.get("/", (req, res, next) => {
    res.sendFile(path.join(public, "/views/index.html"));
  });

  // Serve static files
  app.get("/url", (req, res, next) => {
    res.sendFile(path.join(public, "/views/url.html"));
  });

  // Create short URL from original URL
  app.post("/url", (req, res, next) => {
    console.debug(req.body.url);

    let url = req.body.url;
    const urlId = shortId.generate();

    if (!validUrl.isWebUri(url)) {
      res.status(404).json({ error: "invalid url" });
    } else {
      let urlObj = new URL(url);
      let hostname = urlObj.hostname;
      dns.lookup(hostname, async (err, address, family) => {
        if (err) {
          res.json({ error: "invalid url" });
        } else {
          try {
            let findOne = await urlSchema.findOne({ original_url: url });
            if (findOne) {
              res.json({
                original_url: findOne.original_url,
                short_url: findOne.short_url,
              });
            } else {
              findOne = new urlSchema({ original_url: url, short_url: urlId });
              await findOne.save((err, data) => {
                if (err) {
                  res.json({ error: "invalid url" });
                } else {
                  res.json({
                    original_url: data.original_url,
                    short_url: data.short_url,
                  });
                }
              });
            }
          } catch (err) {
            console.error(err);
            res.status(500).json({ error: "invalid url" });
          }
        }
      });
    }
  });

  // Redirect to original URL from short URL
  app.get("/url/:id", async (req, res, next) => {
    const urlId = req.params.id;
    try {
      let findId = await urlSchema.findOne({ short_url: urlId });
      if (findId) {
        redirectUrl = findId.original_url;
        res.redirect(redirectUrl);
      } else {
        res.json({ error: "L'url est invalide" });
      }
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: "Server error" });
    }
  });

  app.get("/*", (req, res, next) => {
    res.status(404).json({ error: "Page not found" });
  });
}; // End of module.exports
