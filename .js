const mongoose = require('mongoose');

const BookingSchema = new mongoose.Schema({
  personNumber: {
    type: Number,
    required: true,
  },
  address: {
    type: String,
    required: true,
  },
  cost: {
    type: Number,
    required: true,
  },
  createdAt: {
    type: Date,
    default: Date.now,
  },
});

module.exports = mongoose.model('Booking', BookingSchema);