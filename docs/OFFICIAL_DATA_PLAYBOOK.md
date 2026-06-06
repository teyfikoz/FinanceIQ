# Official Data Playbook

FundPilot's public macro spine should prefer official sources over mirrors whenever a stable public interface exists.

## Official sources in production

- `FRED`
  - Base: `https://api.stlouisfed.org/fred`
  - Examples:
    - `WALCL`
    - `M2SL`
    - `ECBASSETSW`
    - `JPNASSETS`
- `U.S. Treasury Fiscal Data`
  - Base: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service`
  - Examples:
    - `/v2/accounting/od/debt_to_penny`
    - `/v1/accounting/dts/operating_cash_balance`
- `TCMB EVDS3`
  - Live JSON base: `https://evds3.tcmb.gov.tr/igmevdsms-dis`
  - Important note:
    - the legacy `service/evds/...` examples often return the EVDS3 SPA shell instead of JSON
    - FundPilot should use the `igmevdsms-dis` endpoints directly

## EVDS3 endpoints used by FundPilot

- Metadata by datagroup:
  - `GET /serieList/fe/type=json&code=<datagroup>`
- Frequency/date helper:
  - `POST /serieList/baslangicBitis`
- Data fetch:
  - `POST /fe`

## EVDS3 payload notes

- Send `key: <TCMB_EVDS_API_KEY>` as a request header when available.
- `POST /fe` works best with an explicit payload that includes:
  - `series`
  - `aggregationTypes`
  - `formulas`
  - `startDate`
  - `endDate`
  - `frequency`
  - `decimalSeperator`
  - `decimal`
  - `dateFormat`
  - `lang`

## Current TCMB series wired into FundPilot

- `TP.AB.C1` → Gold Reserves
- `TP.AB.C2` → FX Reserves
- `TCMB_RESERVES_TOTAL` → derived total reserves from `TP.AB.C1 + TP.AB.C2`

## Environment variables

```bash
FRED_API_KEY=...
TCMB_EVDS_API_KEY=...
TCMB_EVDS_BASE_URL=https://evds3.tcmb.gov.tr/igmevdsms-dis
TREASURY_FISCALDATA_BASE_URL=https://api.fiscaldata.treasury.gov/services/api/fiscal_service
```
