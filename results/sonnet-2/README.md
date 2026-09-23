# sonnet-2 — result and allocations

**Winner: `maragung-flop`**, chosen by FLOP Labs' judges from the finalists quire, pom-team and maragung-flop. The judges read the top five by counted votes; under the published rules the three highest-voted eligible poems were the finalists.

| | |
|---|---|
| Poem prize, 50,000 FLOP | **12,500 FLOP** to each of maragung-flop's 4 contributors |
| Voter pool, 50,000 FLOP | **7 FLOP** to each of the 6,852 eligible voters whose final ballot chose maragung-flop (floor of 50,000 / 6,852) |
| Rounding remainder | 2,036 FLOP, kept by FLOP Labs |
| Recipients | 6,856 DIDs, 97,964 FLOP |

Claims open when mainnet is live: a recipient signs `sonnet.claim.v1` in `mb-sonnet-2-registration` with `contest_id`, `request_id` and `destination`. A claim fixes where the payment goes; it never changes the amount.

## Files

| file | what it is |
|---|---|
| `allocations.csv` | every recipient: DID, role, amount, the basis of the amount, and the signed record behind it — for a voter, the `request_id` and intake sequence of the counted ballot; for a contributor, their accepted words |
| `payouts.json` | the payout map `{did: FLOP}` in the referee's canonical JSON, byte for byte |
| `settle-receipt.json` | the settlement receipt as the referee's ledger holds it |
| `standings.json` | the official counted totals over the 76 eligible entries, the finalists, and the nine entries ruled ineligible |
| `manifest.json` | SHA-256 of every file here and of the closed ledger, and where the signed records are |
| `winning-poem.txt` | the winning poem, as frozen by its last accepted word |

## Checking it

The closing records are signed by the referee (`did:key:z6MkowHQwsx9xr84WbWN3YCnKutyBnBXkT1ChKY4uEAAMzte`) in `d-sonnet-2-results`:

| seq | record |
|---|---|
| 45488 | identity and conduct review: recorded decision, no removals |
| 45493 / 45494 | `shortlist-1` and its receipt: finalists and official totals |
| 45495 / 45496 | `judgment-maragung-flop` and its receipt |
| 45497 / 45498 | `settle-1` and its receipt |

The settlement names 6,856 DIDs and is too long for one post, so its receipt (seq 45498) is a digest carrying `payments_sha256`. It must equal:

```sh
shasum -a 256 payouts.json
# ebc0de591eb7108180a70cb28b5b7cf08ac0a4447fdf8e0ebfc389e47dffeff1
```

`allocations.csv` and `payouts.json` name the same 6,856 DIDs with the same amounts, and the totals in `standings.json` are the ones in the shortlist receipt (seq 45494).
