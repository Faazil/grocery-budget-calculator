# Grocery Budget Calculator

Static site built from USDA Food Plan data.

- Data: `src/data.py` (update monthly from https://www.fns.usda.gov/cnpp/usda-food-plans-cost-food-monthly-reports)
- Build: `python3 src/build.py` -> `public/`
- Deploy: `npx vercel --prod` (Vercel runs the build: build command `python3 src/build.py`, output `public`)
- Env (optional): `SITE_URL`, `CONTACT_EMAIL`
