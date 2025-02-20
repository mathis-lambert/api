db = db.getSiblingDB('api-database');
db.createCollection('users');

const adminApiPassword = process.env.ADMIN_API_PASSWORD;

if (!adminApiPassword) {
    throw new Error('La variable d\'environnement USER_PASSWORD n\'est pas définie.');
}

db.users.insert({
    name: 'admin',
    password: adminApiPassword,
    email: 'mathislambert.dev@gmail.com',
    admin: true,
    disabled: false,
    created_at: new Date(),
    updated_at: new Date()
});
