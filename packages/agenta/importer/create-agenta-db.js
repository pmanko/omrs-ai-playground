const { Pool } = require('pg');

const user = process.env.POSTGRES_USER || 'postgres';
const host = process.env.POSTGRES_SERVICE || 'localhost';
const database = process.env.POSTGRES_DATABASE || 'postgres';
const password = process.env.POSTGRES_PASSWORD || 'instant101';
const port = process.env.POSTGRES_PORT || 5432;
const newDb = process.env.AGENTA_POSTGRESQL_DATABASE || 'agenta';
const newUser = process.env.AGENTA_POSTGRESQL_USERNAME || 'agenta';
const newUserPassword = process.env.AGENTA_POSTGRESQL_PASSWORD || 'agenta123';

const pool = new Pool({
  user,
  host,
  database,
  password,
  port
});

(async () => {
  const client = await pool.connect();

  try {
    // Check if database exists
    const dbResult = await client.query('SELECT 1 FROM pg_database WHERE datname = $1', [newDb]);

    if (!dbResult.rows.length) {
      // Check if user exists
      const userResult = await client.query('SELECT 1 FROM pg_user WHERE usename = $1', [newUser]);

      if (!userResult.rows.length) {
        await client.query(`CREATE USER ${newUser} WITH ENCRYPTED PASSWORD '${newUserPassword}';`);
        console.log(`User '${newUser}' created successfully`);
      } else {
        console.log(`User '${newUser}' already exists`);
      }

      await client.query(`CREATE DATABASE ${newDb};`);
      console.log(`Database '${newDb}' created successfully`);

      // Grant privileges to user
      await client.query(`GRANT ALL PRIVILEGES ON DATABASE ${newDb} TO ${newUser};`);
      console.log(`Granted privileges on '${newDb}' to '${newUser}'`);
    } else {
      console.log(`Database '${newDb}' already exists`);
    }
  } catch (error) {
    console.error('Error creating Agenta database:', error.message);
    process.exit(1);
  } finally {
    client.release();
    pool.end();
  }
})();

