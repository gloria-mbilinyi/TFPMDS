# Optional demonstration database

`tfpmds-demo.sqlite` is an optional synthetic snapshot using the final SQLAlchemy schema. It preserves the genuine completed browser journey alongside the original seed examples. It contains no real transactions, SMS deliveries, provider credentials or JWT secret. Passwords are Argon2 hashes of the documented public demo password `DemoPass123!`. Expired/session-revocation records are excluded. `snapshot-info.json` records actual row counts.

The application normally creates `tfpmds.db` in the repository root and seeds it from versioned source. To inspect this snapshot directly, stop your TFPMDS backend and select its absolute path through `DATABASE_URL` in the root `.env`, or work on a copy in another directory. Never overwrite a database containing your own work.

Example optional configuration (replace the path with your own):

```text
DATABASE_URL=sqlite:///C:/path/to/TFPMDS/demo/tfpmds-demo.sqlite
```

Use this for a local demonstration only. The fresh automated tests use temporary databases, and the seed-based installation does not require this snapshot. The exporter refuses non-demo email domains and refuses to overwrite an existing release snapshot.
