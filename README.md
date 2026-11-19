# Bitcoin Intelligence

A Persian, responsive Bitcoin news dashboard with hourly RSS collection, source-weighted ranking, duplicate filtering, optional AI Persian summaries, and optional Telegram delivery.

## What runs automatically
- GitHub Actions runs at minute 7 of every hour (UTC).
- Collects from CoinDesk, Cointelegraph, Bitcoin Magazine, Decrypt, The Block, Blockworks, Bitcoin.com, Glassnode and Bitwise RSS feeds.
- Filters Bitcoin-relevant stories from the last 72 hours, ranks by source reliability, freshness and topic relevance, then selects up to 10.
- Publishes `public/data.json` and deploys the dashboard to GitHub Pages.
- If configured, OpenAI generates Persian headlines, summaries, importance notes, topic labels and cautious directional tags.
- If Telegram secrets are configured, the same briefing is sent to a Telegram chat.

## Required GitHub setup
1. Upload the project files to the repository root.
2. In **Settings → Actions → General → Workflow permissions**, select **Read and write permissions** and save. This is important because the previous GitHub integration hit `403 Resource not accessible by integration`.
3. In **Settings → Pages**, set **Build and deployment → Source** to **GitHub Actions**.
4. In **Settings → Secrets and variables → Actions**, add:
   - `OPENAI_API_KEY` (recommended for Persian summaries; without it, raw source titles/descriptions are shown)
   - `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` (optional)
5. Go to **Actions → Hourly Bitcoin Intelligence → Run workflow** for the first run.

After the first successful deployment, the dashboard URL is:
`https://ghadimi1989.github.io/Crypto-news-intelligence/`

## Notes
- GitHub scheduled workflows are not guaranteed to start at the exact minute; the `7 * * * *` schedule avoids the top-of-hour congestion.
- RSS availability and source terms/rate limits may change.
- Bias labels are automated editorial estimates, not price forecasts or trading signals.
- X and YouTube are not scraped in this MVP because reliable access generally requires platform/API credentials. The initial build uses publisher RSS sources; X/YouTube adapters can be added when credentials or permitted feeds are available.
