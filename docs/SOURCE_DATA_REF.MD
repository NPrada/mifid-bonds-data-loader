# Data Reference
  Schema: ISO 20022 auth.017.001.02 (MiFIR Reference Data)

  Each <RefData> element is one (ISIN, trading venue) combination — the same ISIN can appear multiple times if it trades on multiple venues.

  ---
  Fields per record

  <FinInstrmGnlAttrbts> — General instrument attributes

  ┌────────────────┬──────────────────────────────┬────────────────────────────────────┐
  │    XML tag     │           Meaning            │              Example               │
  ├────────────────┼──────────────────────────────┼────────────────────────────────────┤
  │ Id             │ ISIN                         │ XS0154960537                       │
  ├────────────────┼──────────────────────────────┼────────────────────────────────────┤
  │ FullNm         │ Full instrument name         │ ENTINN 5.659 06/30/27              │
  ├────────────────┼──────────────────────────────┼────────────────────────────────────┤
  │ ShrtNm         │ Short name (35 chars max)    │ THE UNIQUE PUB/5.659ASST BKD AMORT │
  ├────────────────┼──────────────────────────────┼────────────────────────────────────┤
  │ ClssfctnTp     │ CFI code (6 chars)           │ DAFGAB                             │
  ├────────────────┼──────────────────────────────┼────────────────────────────────────┤
  │ NtnlCcy        │ Notional currency (ISO 4217) │ GBP                                │
  ├────────────────┼──────────────────────────────┼────────────────────────────────────┤
  │ CmmdtyDerivInd │ Commodity derivative flag    │ false                              │
  └────────────────┴──────────────────────────────┴────────────────────────────────────┘

  <Issr> — LEI of the issuer (20-char alphanumeric)

  <TradgVnRltdAttrbts> — Trading venue info

  ┌──────────────────────┬───────────────────────────────────────┐
  │       XML tag        │                Meaning                │
  ├──────────────────────┼───────────────────────────────────────┤
  │ Id                   │ MIC code of the trading venue         │
  ├──────────────────────┼───────────────────────────────────────┤
  │ IssrReq              │ Whether issuer requested admission    │
  ├──────────────────────┼───────────────────────────────────────┤
  │ AdmssnApprvlDtByIssr │ Admission approval date (optional)    │
  ├──────────────────────┼───────────────────────────────────────┤
  │ ReqForAdmssnDt       │ Request for admission date (optional) │
  ├──────────────────────┼───────────────────────────────────────┤
  │ FrstTradDt           │ First trade date                      │
  ├──────────────────────┼───────────────────────────────────────┤
  │ TermntnDt            │ Termination/expiry date               │
  └──────────────────────┴───────────────────────────────────────┘

  <DebtInstrmAttrbts> — Debt-specific fields

  ┌──────────────────────────────┬─────────────────────────────────────────────────┬────────────────────────┐
  │           XML tag            │                     Meaning                     │        Example         │
  ├──────────────────────────────┼─────────────────────────────────────────────────┼────────────────────────┤
  │ TtlIssdNmnlAmt (+ Ccy)       │ Total issued nominal amount                     │ 535000000 GBP          │
  ├──────────────────────────────┼─────────────────────────────────────────────────┼────────────────────────┤
  │ MtrtyDt                      │ Maturity date                                   │ 2027-06-30             │
  ├──────────────────────────────┼─────────────────────────────────────────────────┼────────────────────────┤
  │ NmnlValPerUnit (+ Ccy)       │ Face value per unit                             │ 1000 GBP               │
  ├──────────────────────────────┼─────────────────────────────────────────────────┼────────────────────────┤
  │ IntrstRate/Fxd               │ Fixed interest rate %                           │ 5.659                  │
  ├──────────────────────────────┼─────────────────────────────────────────────────┼────────────────────────┤
  │ IntrstRate/Fltg/RefRate/ISIN │ Reference rate ISIN (for floaters)              │ EU0009652783 (Euribor) │
  ├──────────────────────────────┼─────────────────────────────────────────────────┼────────────────────────┤
  │ IntrstRate/Fltg/Term         │ Tenor of reference rate                         │ 3 MNTH                 │
  ├──────────────────────────────┼─────────────────────────────────────────────────┼────────────────────────┤
  │ IntrstRate/Fltg/BsisPtSprd   │ Spread over reference rate (bps)                │ 120                    │
  ├──────────────────────────────┼─────────────────────────────────────────────────┼────────────────────────┤
  │ DebtSnrty                    │ Seniority — only value seen: SNDB (Senior Debt) │ SNDB                   │
  └──────────────────────────────┴─────────────────────────────────────────────────┴────────────────────────┘

  <DerivInstrmAttrbts> — Derivative overlay (structured products only)

  ┌─────────────────────────┬────────────────────────┐
  │         XML tag         │        Meaning         │
  ├─────────────────────────┼────────────────────────┤
  │ UndrlygInstrm/Bskt/ISIN │ Underlying basket ISIN │
  └─────────────────────────┴────────────────────────┘

  <TechAttrbts> — Technical/administrative

  ┌────────────────────┬──────────────────────────────────────────────────────┐
  │      XML tag       │                       Meaning                        │
  ├────────────────────┼──────────────────────────────────────────────────────┤
  │ RlvntCmptntAuthrty │ Responsible NCA country (ISO 3166, e.g. DE, IE, LU)  │
  ├────────────────────┼──────────────────────────────────────────────────────┤
  │ PblctnPrd/FrDt     │ Date this record became valid (use as ValidFromDate) │
  ├────────────────────┼──────────────────────────────────────────────────────┤
  │ RlvntTradgVn       │ Primary relevant trading venue MIC                   │
  └────────────────────┴──────────────────────────────────────────────────────┘

  ---
  CFI code structure (ClssfctnTp)

  For D (Debt) instruments the 6-letter CFI code breaks down as:
  - Pos 1 D = Debt
  - Pos 2 A=Bonds, B=Convertible bonds, C=Bonds with warrants, F=Medium-term notes, etc.
  - Pos 3 Interest type: F=Fixed, V=Variable/floating, Z=Zero coupon, N=Not applicable
  - Pos 4 Guarantee: G=Guaranteed, U=Unguaranteed, etc.
  - Pos 5 Redemption: A=At maturity, B=Callable, C=Puttable, etc.
  - Pos 6 Form: B=Bearer, R=Registered, N=Bearer/Registered
