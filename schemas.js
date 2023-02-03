const mongoose = require("mongoose");

const Schema = mongoose.Schema;

const urlSchema = new Schema({
  original_url: { type: String, required: true },
  short_url: { type: String, required: true },
});

const IoTSchema = new Schema({
  timestamp: { type: Date, required: true },
  values: {
    temperature: { type: Number, required: true },
    humidity: { type: Number, required: true },
    pressure: { type: Number, required: true },
  },
});

module.exports = mongoose.model("urlModel", urlSchema);
module.exports = mongoose.model("IoTModel", IoTSchema);
