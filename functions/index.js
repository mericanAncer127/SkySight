const cors = require('cors')({ origin: true });

// The Cloud Functions for Firebase SDK to create Cloud Functions and setup triggers.
const functions = require('firebase-functions');

// The Firebase Admin SDK to access Cloud Firestore.
const admin = require('firebase-admin');
admin.initializeApp();

// Set your secret key. Remember to switch to your live secret key in production!
// See your keys here: https://dashboard.stripe.com/account/apikeys
const stripe = require('stripe')('sk_test_51HodZxEjZD5yOZvDKNtQRn1I9JrfUXUJzWGJi71WRXNYHVTK3j3gxsluLZmQfrx7pbWXJJuARVvPUef9jrvbl3RT00kCtH4LBu');

exports.checkout = functions.https.onRequest(async(req, res) => {
    const session = await stripe.checkout.sessions.create({
        payment_method_types: ['card'],
        line_items: [{
            price_data: {
                currency: 'usd',
                product_data: {
                    name: 'Roof Report',
                },
                unit_amount: 1500,
            },
            quantity: 1,
        }, ],
        mode: 'payment',
        success_url: 'https://skysightdata.com/success.html',
        cancel_url: 'https://skysightdata.com',
    });

    res.json({ id: session.id });
});