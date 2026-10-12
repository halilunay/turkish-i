# turkish-i

**A catalog of real bugs caused by the Turkish letters I, ı, İ, i, with a copy-paste reproduction and the upstream fix for each.**

[Türkçe aşağıda](#türkçe)

Turkish has four "i"s: dotted `İ`/`i` and dotless `I`/`ı`. Most case-conversion, comparison and regex code assumes `I` ↔ `i`. Under a Turkish locale that assumption flips (`"LIST".toLowerCase()` → `"lıst"`), and outside a Turkish locale `İ` lowercases to two code points (`i` + U+0307), so `"İstanbul"` never matches `"istanbul"`. Every language has hit this; every project rediscovers it. This repository collects the real cases in one place so maintainers can test against them and developers can find "my bug" and its known fix.

This is not a library. It is data: one YAML file per bug, validated in CI, every file linked to the issue, PR or commit that proves it happened.

## What a record looks like

```yaml
id: python-casefold-dotted-i-notebooklm-py
title: "Title lookup by casefold() cannot find \"İstanbul notları\" with the query \"istanbul\""
language: python
library: notebooklm-py
operation: casefold          # lower, upper, casefold, compare, regex-range, sort, slug, title-case, other
letters: ["İ", "i"]          # which of I ı İ i
locale_dependent: false      # false = breaks everywhere; true = only under tr_TR
input: ...
expected: ...
actual: ...
reproduction:
  command: |
    python3 -c 't="İstanbul notları"; q="istanbul"; print(t.casefold().startswith(q.casefold()))'
  environment: "Python 3.13, Linux"
upstream:
  url: https://github.com/teng-lin/notebooklm-py/issues/2476
  status: open               # open, fixed, wontfix, by-design, unknown
  fix: "drop U+0307 after casefold()"
verification:
  status: verified           # a person or a named AI tool ran the command and saw `actual`
  by: "claude-code (AI), reviewed by halilunay"
  date: 2026-10-12
```

Full rules: [`schema/record.schema.json`](schema/record.schema.json). All records: [`records/`](records/).

## Records so far

| Record | Language | Breaks | Locale-dependent | Upstream status |
| --- | --- | --- | --- | --- |
| [python-casefold-dotted-i-notebooklm-py](records/python-casefold-dotted-i-notebooklm-py.yml) | Python | `casefold()` title lookup | no | open |
| [bash-grep-bracket-range-tr-locale-gstack](records/bash-grep-bracket-range-tr-locale-gstack.yml) | bash / GNU grep | `[a-z]` rejects `i` | yes | fixed |
| [python-lower-dotted-i-cpython](records/python-lower-dotted-i-cpython.yml) | Python | `"İ".lower()` is 2 code points | no | by design |
| [java-tolowercase-default-locale-openjdk-jmod](records/java-tolowercase-default-locale-openjdk-jmod.yml) | Java | `jmod list` mode not recognised | yes | fixed |
| [java-tolowercase-default-locale-apache-spark](records/java-tolowercase-default-locale-apache-spark.yml) | Java / Spark | `SERDEINFO` → `serdeınfo` | yes | fixed |
| [rust-to-lowercase-dotted-i](records/rust-to-lowercase-dotted-i.yml) | Rust | `to_lowercase()` of `İ` | no | won't fix |
| [javascript-tolocalelowercase-tr-locale-scule](records/javascript-tolocalelowercase-tr-locale-scule.yml) | JavaScript | identifiers get `ı`/`İ` | yes | fixed |
| [php-mb-strtolower-dotted-i](records/php-mb-strtolower-dotted-i.yml) | PHP | `mb_strtolower("İ")` | no | by design |

## The two shapes of the bug

1. **Locale-independent** (`locale_dependent: false`): the default Unicode mapping turns `İ` (U+0130) into `i` + U+0307. Python, JavaScript, Rust, PHP, Ruby all do this. Lowercase queries never match titles with `İ`. Known fix: strip U+0307 after `lower()`/`casefold()` when the İ/i pair is all you need, or use a locale-aware API (ICU).
2. **Locale-dependent** (`locale_dependent: true`): the process runs under `tr_TR`, and code that lowercases *machine* text (config keys, enum names, SQL identifiers) gets `ı` instead of `i`, or POSIX ranges like `[a-z]` stop containing `i`. Known fix: `Locale.ROOT` (Java), `LC_ALL=C` (shell), `toLowerCase()` not `toLocaleLowerCase()` (JS) for identifiers; the locale-aware call only for text shown to people.

## Add a record (about 10 minutes)

1. Copy [`records/_template.yml`](records/_template.yml) to `records/<language>-<operation-or-api>-<project>.yml`.
2. Fill the fields. The upstream link is required: an issue, PR, commit or bug-tracker page.
3. Run the reproduction if you can (or have an AI tool run it and name it) and set `verification.status: verified` with `verification.by` saying who ran it; otherwise `unverified` with a note.
4. Open a pull request. CI runs `scripts/validate.py`; a maintainer checks the link and merges.

Details and the review checklist: [CONTRIBUTING.md](CONTRIBUTING.md). Have a bug but no time for a PR? Open an issue with the [new record template](.github/ISSUE_TEMPLATE/new-record.md).

## Use the catalog in your tests

Each record's `input`/`expected`/`actual` is the test case; `reproduction.command` is the oracle. A ten-line runner in your language that loads `records/*.yml`, filters by `language` and asserts your own function on `input` is the intended use. Runners for popular languages are a welcome contribution (label `runner`).

## License

MIT. See [LICENSE](LICENSE).

---

## Türkçe

**Türkçenin dört "i"si (I, ı, İ, i) yüzünden çıkan gerçek hataların kataloğu: her kayıtta kopyala-yapıştır bir yeniden üretim ve upstream'deki düzeltme.**

Bu bir kütüphane değil, veri: her hata bir YAML dosyası, hepsi CI'da denetleniyor, her dosya hatanın gerçekten olduğunu gösteren issue, PR ya da commit'e bağlı.

Hatanın iki biçimi var:

1. **Yerel ayardan bağımsız:** Unicode'un varsayılan eşlemesi `İ`yi `i` + U+0307'ye (birleşik nokta) çevirir. Python, JavaScript, Rust, PHP, Ruby hepsi böyle. Küçük harfli arama `İ`li başlığı bulamaz. Bilinen düzeltme: `lower()`/`casefold()` sonrası U+0307'yi at ya da yerel ayara duyarlı bir API (ICU) kullan.
2. **Yerel ayara bağlı:** program `tr_TR` altında çalışır; makine metnini (ayar anahtarı, enum adı, SQL tanımlayıcı) küçülten kod `i` yerine `ı` alır ya da `[a-z]` aralığı `i`yi kapsamaz olur. Bilinen düzeltme: `Locale.ROOT` (Java), `LC_ALL=C` (kabuk), tanımlayıcılarda `toLocaleLowerCase()` değil `toLowerCase()` (JS); yerel ayara duyarlı çağrı yalnız insana gösterilen metinde.

**Kayıt eklemek (yaklaşık 10 dakika):** `records/_template.yml` dosyasını `records/<dil>-<işlem>-<proje>.yml` adıyla kopyala, alanları doldur (upstream bağlantısı zorunlu), yeniden üretimi bir kişi ya da adını yazdığın bir yapay zekâ aracı koştuysa `verified` yaz ve kimin koştuğunu `verification.by` alanına ekle (`halilunay` ya da `claude-code (AI), reviewed by halilunay`), koşulamadıysa `unverified` + not; PR aç. CI `scripts/validate.py`'yi çalıştırır; bakımcı bağlantıya bakıp birleştirir. Ayrıntı: [CONTRIBUTING.md](CONTRIBUTING.md). PR açacak vaktin yoksa issue şablonuyla bildir, biz kayda çeviririz.

Lisans: MIT.
