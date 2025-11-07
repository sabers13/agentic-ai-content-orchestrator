# Troubleshooting

## 1. WordPress.com 401 / 403
- Check `.env` has `WP_DOTCOM_BEARER=...`
- Check `WP_DOTCOM_API_BASE=https://public-api.wordpress.com/wp/v2/sites/<yoursite>.wordpress.com`
- Re-run: `python -m src.publisher.cli --input data/final/<file>.json --status draft`

## 2. Quality Agent rejects everything
- Check `.env` thresholds: lower to `QUALITY_THRESHOLD=70`
- Or simplify draft: `python scripts/simplify_draft.py data/optimized/<file>.json`

## 3. Prefect inside Docker cannot reach API
- Set env in Dockerfile: `ENV PREFECT_API_URL=""`

## 4. Nothing in dashboard
- Make sure `data/runs.sqlite` exists — run: `python -m src.llm_compare.cli --brief "test"` once
- Start dashboard: `streamlit run src/dashboard/app.py`
