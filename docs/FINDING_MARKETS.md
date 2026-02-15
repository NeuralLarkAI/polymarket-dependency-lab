# Finding Polymarket Market Token IDs

To use live data with this bot, you need to specify real Polymarket market token IDs in your `config.yaml`.

## How to Find Token IDs

### Method 1: Using the Polymarket Website

1. Go to [Polymarket.com](https://polymarket.com)
2. Browse to a market you're interested in
3. Look at the URL - it will contain the market identifier
4. The token IDs are embedded in the market data

### Method 2: Using the Polymarket API

You can fetch active markets using the Polymarket Gamma API:

```python
import requests

# Get active markets
response = requests.get('https://gamma-api.polymarket.com/markets?active=true&limit=10')
markets = response.json()

# Print market info
for market in markets:
    print(f"Question: {market['question']}")
    if 'tokens' in market:
        for token in market['tokens']:
            print(f"  Token ID: {token['token_id']}")
            print(f"  Outcome: {token['outcome']}")
    print()
```

### Method 3: Using py-clob-client

The py-clob-client library can also be used to discover markets:

```python
from py_clob_client.client import ClobClient

client = ClobClient(host="https://clob.polymarket.com", key="")

# You can get order books for specific token IDs
token_id = "your_token_id_here"
book = client.get_order_book(token_id)
print(book)
```

## Example Market Token IDs

Here are some example formats of Polymarket token IDs:

```yaml
markets:
  # Token IDs are long hexadecimal strings
  token_a: "21742633143463906290569050155826241533067272736897614950488156847949938836455"
  token_b: "71321045679252212594626385532706912750332728571942532289631379312455583992563"
```

## Choosing Markets for Dependency Trading

When selecting markets for dependency trading, look for:

1. **Related Events**: Markets that logically depend on each other
   - Example: "Candidate A wins primary" and "Candidate A wins general election"
   - Example: "Team X makes playoffs" and "Team X wins championship"

2. **Sufficient Liquidity**: Both markets should have enough trading volume
   - Check the order book depth before trading
   - Higher liquidity = better fills

3. **Active Markets**: Markets that are still open for trading
   - Avoid markets that have already resolved
   - Check the end date

## Testing Your Configuration

After updating your `config.yaml` with real token IDs, test the connection:

```bash
# Run the bot for a few seconds
timeout 10 python3 run.py
```

You should see:
```
[APP] Starting with LIVE Polymarket data feed
[APP] Market A: <your_token_id>
[APP] Market B: <your_token_id>
[LIVE FEED] Starting live feed for 2 markets
```

If you see errors about token IDs not found, the IDs may be invalid or the markets may have closed.
