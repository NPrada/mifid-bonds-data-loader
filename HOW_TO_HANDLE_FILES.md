# FIRDS Reference Data System

## Instructions on download and use of full, delta and cancellations reference data files

**Document:** ESMA65-8-5014 rev 3
**Date:** 09 February 2022

---

## Table of Contents

1. [Introduction](#introduction)
2. [Description of Reference Data Files](#description-of-reference-data-files)
3. [Instructions to Download Files](#instructions-to-download-files)
4. [Use of Full, Delta and Cancellations Files](#use-of-full--delta-and-cancellations-files)
5. [Use of Other Reference Data Files](#use-of-other-reference-data-files)

---

## Introduction

### 1.1 Purpose and Intended Audience

The purpose of this document is to provide details on the reference data files that ESMA will be publishing and how to access them, and how to use them.

The intended audience are the EU market participants that need to make use of the instrument reference data for the purpose of MiFIR, as well as National Competent Authorities from EU and EEA countries.

**Note:** Paragraphs highlighted in blue are applicable to National Competent Authorities only and will be removed from the document published to avoid confusion.

### 1.2 Scope

The scope of this document is the instruments reference data files.

### 1.3 Abbreviations

| Acronym | Definition |
|---------|------------|
| RM | Regulated Market |
| MTF | Multilateral Trading Facility |
| OTF | Organised Trading Facility |
| SI | Systematic Internaliser |

---

## Description of Reference Data Files

### 2.1 File Types

The system makes reference data available in the form of machine-readable files:

#### Full File
The full file contains the full reference data received by ESMA before the applicable cut-off time, for all instruments that are still active and that have been admitted to trading on RM, including where a request for admission to trading has been made, or that are traded on a MTF, OTF, or SI.

#### Delta File
The delta file contains all records for which a change has occurred (addition, modification, deletion) since the generation of the last set of files. Changes can occur in the following situations:

- An instrument starts being traded on a trading venue: new (ISIN, MIC) - `<NewRcrd>`
- An instrument ceases being traded on a trading venue: the (ISIN, MIC) is terminated - `<TermntdRcrd>`
- A modification has been made in the reference data fields or in the relevant competent authority for the instrument - `<ModfdRcrd>`
- An instrument is being cancelled on a trading venue: the (ISIN, MIC) is cancelled - `<CancRcrd>`

**Note:** In exceptional cases, some of these records may relate to instruments that were already terminated. For example, it may be that an ISIN-MIC is reported for the first time very late, after it was terminated, or may undergo a correction in its reference data, after it was terminated. In these cases the corresponding record will only be available in the Delta / Invalid records file and will not appear in the Full file.

#### Invalid Records File
This file contains all records that are not part of the full file anymore and, in exceptional cases, records that were never published as part of the full file. This includes instruments that are not valid anymore, as well as out-of-date versions of records that have been modified over time.

For Delta files, in exceptional cases it will also contain records of instruments that are reported for the first time after they are terminated, or modifications that are made on instruments after they are terminated. In these exceptional cases the corresponding record will only be available in the Delta / Invalid records file and will not appear in the Full file.

#### Cancelled Records File
This file contains the full set of consolidated cancelled reference data which has been submitted to ESMA before the applicable cut-off time submitted on the previous working day by Trading Venues, Systematic Internalisers and National Competent Authorities that have not delegated collection. The file contains all cancelled records reported.

### 2.2 Reference Data Fields

The list of reference data fields published by the system includes:

- Fields described in Tables 1, 2 and 3 of the Annex of the Regulatory Technical Standard 23
- The country of the Relevant Competent Authority for the instrument
- For NCAs' full file only:
  - The date / time when the record was last received from the corresponding submitting entity (RefData/TechAttrbts/LastUpd in the full file)
  - A flag indicating whether an inconsistency has been detected for the corresponding record (RefData/TechAttrbts/IncnsstncyInd)

**Note:** Given the high volume of data, the files are split into several files, in particular when they exceed 500,000 records, or based on the first letter of the CFI code in the case of the full file.

---

## Instructions to Download Files

### 3.1 Timing of Generation

The files published by ESMA on its website are generated as follows:

- **Full File:** on a weekly basis - on Sunday morning by 09:00 CET
- **Delta File:** on a daily basis - every morning by 09:00 CET
- **Cancellations File:** on a daily basis - every morning by 09:00 CET

The files provided to NCAs on the HUB are generated on a daily basis.

### 3.2 XML Format

The reference data files produced by FIRDS are structured as follows:

#### File Structure
- **Business Application Header (BAH)** and **Payload** as per XML Schema head.003.001.01.xsd
- **Business Application Header** is generated as per XML Schema head.001.001.01_ESMAUG_1.0.0.xsd
- **Payload** is generated as per XML Schema

#### File Types and Naming

| File Type | Schema |
|-----------|--------|
| Full file | auth.017.001.02_ESMAUG_FULINS_1.1.0.xsd |
| Delta file | auth.036.001.03_ESMAUG_DLTINS_1.2.0.xsd |
| Cancellations file | auth.102.001.01_ESMAUG_CANINS_1.2.0.xsd |

**XML Schema Link:** [V1.2.0](https://www.esma.europa.eu/)

#### File Naming Conventions

##### Full File Naming
```
FULINS_<CFI 1st letter>_<Date>_<Key1>of<Key2>.zip
```

Where:
- `<Date>` = YYYYMMDD
- `<Key1>` = The number of the file in the range produced for that day and that CFI 1st letter
- `<Key2>` = The total number of files produced for that day and that CFI 1st letter

**Examples:**
```
FULINS_C_20170625_01of01.zip
FULINS_D_20170625_01of02.zip
FULINS_D_20170625_02of02.zip
FULINS_E_20170625_01of02.zip
FULINS_E_20170625_02of02.zip
FULINS_F_20170625_01of01.zip
FULINS_H_20170625_01of01.zip
FULINS_J_20170625_01of01.zip
```

##### Delta File Naming
```
DLTINS_<Date>_<Key1>of<Key2>.zip
```

Where:
- `<Date>` = YYYYMMDD
- `<Key1>` = The number of the file within the range produced for that day
- `<Key2>` = The total number of files produced for that day

**Example:**
```
DLTINS_20170624_01of01.zip
```

##### Cancellations File Naming
```
FULCAN_<Date>_<Key1>of<Key2>.zip
```

Where:
- `<Date>` = YYYYMMDD
- `<Key1>` = The number of the file within the range produced for that day
- `<Key2>` = The total number of files produced for that day

**Example:**
```
FULCAN_20170624_01of01.zip
```

### 3.3 Access to Files - Human Interface

To access the FIRDS files via the web interface:

1. Go to https://registers.esma.europa.eu/publication/ and select register "Financial Instrument Reference Data System" then click on "Financial Instruments Reference Files"; or go directly to: https://registers.esma.europa.eu/publication/searchRegister?core=esma_registers_firds_files

2. Use the **Publication Date** filter on the left-hand side and click on "Filter list" to list all files published within the specified period.

### 3.4 Access to Files - Machine-to-Machine Interface

To support automated download of the files, it is possible to list the files published on a specific date by sending an HTTP request.

#### Example HTTP Request

The following HTTP request will return the list of the files published by ESMA on 25 August 2017:

```
https://registers.esma.europa.eu/solr/esma_registers_firds_files/select?q=&fq=publication_date:%5B2017-08-25T00:00:00Z+TO+2017-08-25T23:59:59Z%5D&wt=xml&indent=true&start=0&rows=100
```

#### Query Components Explanation

| Component | Description |
|-----------|------------|
| `q=*` | This is the general query part of the request and tells the response to return all columns for a given result if one exists |
| `fq=publication_date:%5B2017-08-25T00:00:00Z+TO+2017-08-25T23:59:59Z%5D` | `fq` means the filtered query and supports restricting the data that is being search for. For the filtered query here, we are restricting by date – note both the latest date and earliest date are present and follow the ISO date format. Change the date to look for files from a different day or range of days |
| `wt=xml` | Response type e.g. xml, json |
| `indent=true` | Not necessary but assists to make the output more readable |
| `start=0` | The result to start outputting from. 0 works best but any number can be here and corresponds to which set of records to start outputting from |
| `rows=100` | The number of results to return. Default is 10 |

#### Processing Results

The combination of start and row is used to assist cycling over the results when multiple results are returned (e.g. more than 100). To read a secondary list (100+) change start to 100 and leave rows as 100. The number of records that the query returns is given by attributes of the resultsfound list.

The response is an XML document. The URLs to the files are located under the following XPath:

```
/response/result/doc/str[@name='download_link']
```

Note that the number of returned files returned will usually be greater than 1 for a given date.

---

## Use of Full, Delta and Cancellations Files

### 4.1 Background

The reference data associated with each (ISIN, MIC) may undergo modifications over time for the following reasons:

- When an instrument starts being traded, its termination date may not be known and in that case TraddVnRltdAttrbts/TermntnDt will not be present. When the termination date is known, it will be populated.

- The Relevant Competent Authority of the instrument may change over time. For example, RTS 22 foresees that the relevant market is reassessed every year for equity instruments.

- Some information may change over time, e.g. the name of the financial instrument may be updated.

- Reporting entities may send corrections to the data previously submitted.

### 4.2 Building a Historical Database Using FULINS / DLTINS

To build a historical database and be able to support queries described in section 3.4, it is recommended to associate to each record:

- **Validity dates:** ValidFromDate / ValidToDate
- **Latest record flag:** true if the record is the latest version of the record received, false for historical versions of the record.

#### Process for Building Historical Database

**On day T download the FULINS file and register all records:**

1. Register all data for all fields provided under `<RefData>`, including the `<TechAttrbts>` and in particular RefData/TechAttrbts/PblctnPrd/FrDt as ValidFromDate. Leave ValidToDate empty (null).

2. Set the LatestRecordFlag as true

**From day T+1, download the DLTINS file every day, and process as follows:**

For each DLTINS record in `<NewRcrd>`:

1. Insert the content of the DLTINS record in the database, including the `<TechAttrbts>` and in particular:
   - The PblctnPrd child is FrDt: register FrDt as ValidFromDate and leave ValidToDate empty

2. Set the LatestRecordFlag of the new DLTINS record to true

For each DLTINS record with `<ModfdRcrd>`, `<CancRcrd>`:

1. Select the rows of the historical database such that:
   - ISIN = ISIN of the DLTINS record
   - MIC = MIC of the DLTINS record
   - ValidToDate is null

2. Set ValidToDate of these rows to ValidFromDate -1 of the DLTINS record with `<ModfdRcrd>`, `<CancRcrd>`

3. Set LatestRecordFlag of these records to false

4. Insert the content of the DLTINS record in the database, including the `<TechAttrbts>` and in particular:
   - The PblctnPrd child is FrDt: register FrDt as ValidFromDate and leave ValidToDate empty

5. Set the LatestRecordFlag of the new DLTINS record to true

For each DLTINS record in `<TermntdRcrd>`:

1. Select the rows of the historical database such that:
   - ISIN = ISIN of the DLTINS record
   - MIC = MIC of the DLTINS record
   - ValidToDate is null

2. If no record is found in the database (case of terminated instrument reported late):
   - Insert the content of the DLTINS record in the database, including the `<TechAttrbts>` and in particular:
     - The PblctnPrd child is FrDt: register FrDt as ValidFromDate and leave ValidToDate empty

3. Else if a record exists in the database and the ValidFromDate of the selected row is different from the ValidFromDate of the DLTINS record with `<TermntdRcrd>` (case of a correction on an instrument already terminated or terminated through modification):
   - Set ValidToDate of the selected rows to ValidFromDate -1 of the DLTINS record with `<TermntdRcrd>`
   - Set LatestRecordFlag of these records to false
   - Insert the content of the DLTINS record in the database, including the `<TechAttrbts>` and in particular:
     - The PblctnPrd child is FrDt: register FrDt as ValidFromDate and leave ValidToDate empty

4. Else if the ValidFromDate of DLTINS record with `<TermntdRcrd>` is equal to the ValidFromDate of the selected row (case of a normally terminated instrument):
   - Replace the selected row with the DLTINS record with `<TermntdRcrd>`

5. Set the LatestRecordFlag of the new DLTINS record to true

### 4.3 Querying the Historical Database

Once the historical database has been built according to section 4.2, the database can be queried for example as follows:

#### Get Latest Reference Data

To get the latest reference data for all (ISIN, MIC), regardless whether they are terminated or not:

```sql
Select * from <table> where table_ISIN = ISIN and table_MIC = MIC and LatestRecordFlag = true
```

#### Get Active Instruments on Day T

To list the reference data for all (ISIN, MIC) that where active on day T, based on the latest reference data available:

```sql
Select * from <table> where table_ISIN = ISIN and table_MIC = MIC and LatestRecordFlag = true and Field 11 <= T and (Field 12 is null or Field 12 >= T)
```

#### Get Reference Data on Given Day in Past

To know what was the reference data for an (ISIN,MIC) on a given day T in the past:

```sql
Select * from <table> where table_ISIN = ISIN and table_MIC = MIC and ValidFromDate <= T and (ValidToDate is null or ValidToDate >= T)
```

#### Get Active Reference Data on Day T Based on Historical Availability

To list the reference data for all (ISIN, MIC) that where active on day T, based on the reference data that was available on a given day X in the past:

```sql
Select * from <table> where table_ISIN = ISIN and table_MIC = MIC and ValidFromDate <= X and (ValidToDate is null or ValidToDate >= X) and Field 11 <= T and (Field 12 is null or Field 12 >= T)
```

---

## Use of Other Reference Data Files

### 5.1 CFI, MIC, Currency, Country and Index Reference Data

For the CFI, MIC, Currency, Country and Index expression of interest reference data only a single file is produced for each type of data and it includes the currently active as well as inactive reference records. Therefore, the historical database for these files should be equivalent to the file content.

The CFI, MIC, Currency and Country reference data is generated and published on the HUB on weekly basis, every Saturday by 9:00am CET.

The Index expression of interest data is published on the HUB on daily basis.

#### Querying Reference Data

To list the reference data for all reference records that where active on day T in the past, based on the latest reference data available:

- **For CFI:**
  ```sql
  Select * from <CFITable> where CFITable_CFI = CFI and ValidFromDate <= T and (ValidToDate is null or ValidToDate >= T);
  ```

- **For MIC:**
  ```sql
  Select * from <MICTable> where MICTable_MIC = MIC and ValidFromDate <= T and (ValidToDate is null or ValidToDate >= T);
  ```

- **For Currency:**
  ```sql
  Select * from <CurrencyTable> where CurrencyTable_CurrencyCode = CurrencyCode and ValidFromDate <= T and (ValidToDate is null or ValidToDate >= T) and CurrencyTable_CurrencyCode NOT LIKE 'XX_';
  ```

- **For Country:**
  ```sql
  Select * from <CountryTable> where CountryTable_CountryCode = CountryCode and ValidFromDate <= T and (ValidToDate is null or ValidToDate >= T);
  ```

- **For Index:**
  ```sql
  Select * from <IndexTable> where IndexTable_Index = Index and ValidFromDate <= T and (ValidToDate is null or ValidToDate >= T).
  ```

**Note:** The currency data file includes separate records per the combination of currency and country code (i.e. a currency might be valid in more than one country). For the purpose of the transaction data validation it is sufficient that a currency is valid in any country, i.e. at least one record is returned for a given day.

### 5.2 LEI Reference Data

The LEI reference data is provided on daily basis.

The data provided by FIRDS is identical to the data published by GLEIF. This file does not include the full history of LEI; in particular, the history of the LEI status changes. It implies that NCAs shall build the historical database for this data.

#### Querying LEI Reference Data

To list the reference data for a record active on day T in the past:

- **For the purpose of the Executing Entity validation:**
  ```sql
  Select * from <LEITable> where LEITable_LEI = LEI and PublicationDate = T+1 and LEITable_Status in ('Issued', 'Pending transfer', 'Pending archival') and LEITable_InitialRegistrationDate<=T and (LEITable_EntityStatus='Active' or LEITable_LastUpdateDate>=T);
  ```

- **For the purpose of other validations:**
  ```sql
  Select * from <LEITable> where LEITable_LEI = LEI and PublicationDate = T+1 and LEITable_Status in ('Issued', 'Pending transfer', 'Pending archival', 'Lapsed') and LEITable_InitialRegistrationDate<=T and (LEITable_EntityStatus='Active' or LEITable_LastUpdateDate>=T).
  ```

---

## Document Control

| Version | Date | Author | Comments |
|---------|------|--------|----------|
| 1 | 28/09/2017 | ESMA | Version for review by the Markets IT Task Force / FIRDS Delegated Project Task Force |
| 2 | 25/08/2020 | ESMA | Incorporating Cancellations file |
| 2.1 | 04/02/2022 | ESMA | XML v1.2.0 link update |
| 3 | 09/02/2022 | ESMA | Update of section 4.2 to be aligned with the implementations of FIRDS M2 & 3 releases. Addition of missing <CancRcrd> paragraph on chapter 2 (5.b.iv) |

---

## Reference Documents

| Ref | Title | Version | Author | Date |
|-----|-------|---------|--------|------|
| RTS23 | COMMISSION DELEGATED REGULATION (EU) 2017/585 of 14 July 2016 supplementing Regulation (EU) No 600/2014 of the European Parliament and of the Council with regard to regulatory technical standards for the data standards and formats for financial instrument reference data and technical measures in relation to arrangements to be made by the European Securities and Markets Authority and competent authorities | 1 | European Commission / ESMA | 31/03/2017 |
| Reporting Instructions | FIRDS Reference Data System – Reporting Instructions | 2.3 | ESMA | 17/09/2020 |

---

**ESMA** • CS 60747 – 201 - 203 rue de Bercy • 75012 • Paris France • Tel. +33 (0) 1 58 36 43 21 • www.esma.europa.eu