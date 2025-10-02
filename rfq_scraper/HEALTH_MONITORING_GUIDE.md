# RFQ Scraper Health Monitoring & Auto-Repair System

## Overview

The scraper now includes intelligent health monitoring, multi-strategy fallback, and auto-repair capabilities.

## New Features

### 1. **Health Monitoring**
- Tracks historical performance for each city
- Calculates % change from previous runs
- Generates alerts for anomalies

**Alert Levels:**
- 🚨 **Critical**: RFQ count dropped >50% or scrape failed
- ⚠️ **Warning**: RFQ count dropped 25-50%
- ℹ️ **Info**: RFQ count increased >100%
- ✅ **Success**: Normal operation

### 2. **Multi-Strategy Fallback**
When the configured selector fails, the scraper automatically tries:
1. Standard HTML table (`table tbody tr`)
2. Table with specific class (`table.tabHome tbody tr`)
3. Bonfire portal table (`tbody tr`)
4. Div-based opportunity items (`.opportunity-item`)
5. OpenGov opportunity rows (`.opportunity-row`)
6. Generic table rows (`tr`)
7. Div-based rows (`div.row, .item`)

**If a fallback strategy works:**
- The scraper uses it for that run
- Updates `cities.json` with the new selector
- Uses the new selector as default on next run

### 3. **Auto-Updating Configuration**
When a city's website structure changes:
- Scraper detects the issue (0 rows found)
- Tries alternative strategies automatically
- Updates `cities.json` with working strategy
- Logs the change in health report

### 4. **Historical Tracking**
All runs are saved to `scraper_history.json`:
```json
{
  "runs": [
    {
      "timestamp": "2025-10-02T13:00:00",
      "cities": {
        "City of Gilbert": {
          "rfq_count": 31,
          "status": "success",
          "strategy_used": "standard_table"
        }
      },
      "total_rfqs": 41,
      "alerts": []
    }
  ]
}
```

## Files Created

1. **`scraper_health.py`**: Health monitoring module
2. **`scraper_strategies.py`**: Strategy definitions and auto-detection
3. **`scraper_history.json`**: Historical run data (auto-generated)
4. **`scraper_report.txt`**: Latest run report (optional)

## Usage

Run the scraper as before:
```bash
python multi_scraper.py
```

**New output includes:**
- Strategy fallback attempts
- Configuration updates
- Health report at the end

## Example Health Report

```
============================================================
Scraper Health Report - 2025-10-02T13:00:00
============================================================

Total RFQs collected: 41
Cities scraped: 7
Success: 6 | Failed: 1

⚠️  ALERTS (1)
------------------------------------------------------------
⚠️ [WARNING] City of Yuma
   RFQ count dropped 33.3% (3 → 2)

📊 CITY RESULTS
------------------------------------------------------------
✅ City of Gilbert: 31 RFQs [standard_table]
✅ City of Mesa: 11 RFQs [default]
✅ City of Apache Junction: 1 RFQs [default]
⚠️ City of Yuma: 2 RFQs [bonfire_table]
❌ Pinal County: 0 RFQs
   Error: CAPTCHA detected
============================================================
```

## Notification Options

Currently supports:
- **Console** (default): Prints to terminal
- **File**: Saves to `scraper_report.txt`
- **Email**: Placeholder for future implementation

To change notification method, edit line in `multi_scraper.py`:
```python
health_monitor.send_notification(method="file")  # or "console" or "email"
```

## Future Enhancements

**Phase 2** (Easy to add):
- Email notifications via SMTP
- Slack/Discord webhooks
- Automatic retry on failure
- Custom alert thresholds per city

**Phase 3** (Moderate):
- Machine learning to predict scrape failures
- Automatic CAPTCHA solving integration
- API fallback for supported platforms
- Web dashboard for health monitoring

## Troubleshooting

**Q: Scraper keeps switching strategies every run**
A: The website might have dynamic content. Add `"preferred_strategy": "strategy_name"` to lock it.

**Q: Getting too many alerts**
A: Adjust thresholds in `scraper_health.py` (lines 60-80)

**Q: Want to reset history**
A: Delete `scraper_history.json` to start fresh

**Q: City configuration keeps reverting**
A: Check file permissions on `cities.json` - scraper needs write access

