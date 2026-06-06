# AdSense and AdMob Setup Notes

## Use the right Google product

- `AdSense` is for websites.
- `AdMob` is for mobile apps that integrate the Google Mobile Ads SDK.

For `https://fundpilot.techsyncanalytica.com`, use `AdSense`, not `AdMob`.

## Recommended rollout order

1. Keep the current direct sponsor and affiliate slots live first.
2. Add AdSense only after the public pages have stable content and a published privacy/disclosure page.
3. Add a CMP before serving Google ads to EEA, UK, or Swiss users.

## AdSense setup flow

1. Create or sign in to an AdSense account.
2. Add your site in AdSense Sites.
3. Verify ownership with the AdSense code snippet or DNS/HTML verification.
4. Wait until the site status is ready.
5. Create ad units for the placements you actually want to use.
6. Update your privacy/disclosure copy before turning ads on.

## Subdomain note

AdSense site management is domain-oriented. In practice, if you monetize
`fundpilot.techsyncanalytica.com`, review the approval state for `techsyncanalytica.com`
and confirm the subdomain content complies with AdSense policies.

## Compliance warning

Turning on AdSense changes your privacy posture:

- Google ads for EEA, UK, and Swiss users require a Google-certified CMP.
- Your privacy page and disclosure copy need to mention Google ads and consent choices.
- If you keep the current no-tracker posture, do not enable AdSense scripts yet.

## Practical recommendation for this repo

- Keep Google ad network scripts disabled by default.
- Treat direct sponsor cards and affiliate links as the primary low-risk monetization layer.
- Introduce AdSense only after CMP and disclosure work is complete.
