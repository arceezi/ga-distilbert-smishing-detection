# Final Combined Dataset Validation Report

| Dataset | Ham | Smishing | Total | Manual Ham | Synthetic Ham | UCI Ham | Mishra Ham | UCI Ham Share | Issues | Warnings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| V1 | 4954 | 4954 | 9908 | 0 | 0 | 4492 | 462 | 90.67% | None | Duplicate normalized message_raw keys inherited or retained by source selection: 140; Duplicate normalized message_clean keys inherited or retained by source selection: 159 |
| V2 | 5272 | 5272 | 10544 | 320 | 0 | 4490 | 462 | 85.17% | None | Duplicate normalized message_raw keys inherited or retained by source selection: 173; Duplicate normalized message_clean keys inherited or retained by source selection: 271 |
| V3 | 5272 | 5272 | 10544 | 320 | 1112 | 3378 | 462 | 64.07% | None | Duplicate normalized message_raw keys inherited or retained by source selection: 173; Duplicate normalized message_clean keys inherited or retained by source selection: 271 |

## V3 Specific Metrics

- Synthetic ham count: 1112
- Manual ham count: 320
- UCI ham share: 64.07%
- Synthetic ham share: 21.09%
- Manual + synthetic service ham share: 27.16%

## Notes

Synthetic ham messages were generated from manually approved legitimate service-message templates. Unlike collected public data, these messages are synthetic and contain fake/generated values in the raw text field. A privacy-safe cleaned version was also generated for each synthetic message. Synthetic rows are clearly marked with is_synthetic=True and data_origin=synthetic_template.
