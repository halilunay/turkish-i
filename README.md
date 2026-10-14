# turkish-i

**Real cases where the Turkish letters I, ı, İ, i broke code or a user's expectation, each with a copy-paste reproduction, the upstream link and the approach that fits.**

[Türkçe aşağıda](#türkçe)

Turkish has four "i"s: dotted `İ`/`i` and dotless `I`/`ı`. Unicode defines more than one correct way to change their case, and most of these cases come from code using one way where another was needed. This repository collects real, linked cases so maintainers can test against them and developers can find "my case" and the approach that fits.

This is not a library. It is data: one YAML file per case, validated in CI, every file linked to the issue, PR or commit that shows it happened.

## Unicode gives `İ` three conformant lowercase results

| Layer | Source | `İ` lowercases to | Used by (checked 2026-10-14) |
| --- | --- | --- | --- |
| Simple mapping | `UnicodeData.txt` (`0130 … ;0069;`) | `i` | Go `strings.ToLower`, Java `Character.toLowerCase` (but `String.toLowerCase` uses the full mapping), PHP `MB_CASE_LOWER_SIMPLE` |
| Full mapping | `SpecialCasing.txt` (`0130 → 0069 0307`) | `i` + U+0307 | Python `lower()`/`casefold()`, JavaScript `toLowerCase()`, Rust `to_lowercase()`, PHP `mb_strtolower()`, Ruby `downcase` |
| Turkish tailoring (`tr`, `az`) | `SpecialCasing.txt` tr/az rules, `CaseFolding.txt` status `T` | `i`, and `I` → `ı` | JS `toLocaleLowerCase('tr')`, Ruby `downcase(:turkic)`, Go `unicode.TurkishCase`, ICU |

All three conform to the standard: the Unicode Standard (§3.13) says that where an environment requires tailored casing, "use of such tailoring does not violate conformance to the standard", and names the Turkish dotted and dotless i as an example. Trouble starts when code mixes layers: lowercases with one and compares with another, applies Turkish rules to machine text, or folds case without normalizing.

## Three kinds of record

Every record has a `kind`:

- **`bug`**: the code broke the standard or its own intent, and upstream fixed or confirmed it. Typical: a process running under a Turkish locale (`tr_TR`) lowercases *machine* text (config keys, enum names, SQL identifiers) and gets `ı` instead of `i`, or a POSIX range like `[a-z]` stops containing `i`. Approach: `Locale.ROOT` (Java), `LC_ALL=C` (shell), `toLowerCase()` rather than `toLocaleLowerCase()` (JS) for identifiers.
- **`by-design`**: the runtime correctly applies a Unicode default mapping, for example `"İ".lower()` returning `i` + U+0307 in Python. Approach: for Turkish text, use a tailored call (ICU / PyICU, `toLocaleLowerCase('tr')`, Ruby `downcase(:turkic)`).
- **`expectation-gap`**: the code follows the standard, but users expect search-style matching, for example `istanbul` finding `İstanbul`. This is a design decision, not a defect. Approach for matching:
  1. Normalize before and after folding (NFD → casefold → NFC, as in Unicode D145). This also fixes composed vs decomposed text such as `Café`.
  2. If `İstanbul` must match `istanbul`, add an accent-insensitive fallback tier. Note that it also makes `şık` match `sık`, so treat ambiguous results as errors.
  3. Neither step makes `IĞDIR` match `ığdır`. Only Turkish tailoring does that, for example a `tr` collator (`Intl.Collator('tr', {sensitivity: 'accent'})`).

Dropping U+0307 after `i` gives the same result for `İ` as the simple mapping and matches the `tr` After_I rule in `SpecialCasing.txt`. It is lenient rather than wrong, but it is only half of Turkish casing: it does nothing for `I` → `ı`.

## Records so far

| Record | Language | Kind | Locale-dependent | Upstream status |
| --- | --- | --- | --- | --- |
| [bash-grep-bracket-range-tr-locale-gstack](records/bash-grep-bracket-range-tr-locale-gstack.yml) | bash / GNU grep | bug | yes | fixed |
| [java-tolowercase-default-locale-openjdk-jmod](records/java-tolowercase-default-locale-openjdk-jmod.yml) | Java | bug | yes | fixed |
| [java-tolowercase-default-locale-apache-spark](records/java-tolowercase-default-locale-apache-spark.yml) | Java / Spark | bug | yes | fixed |
| [javascript-tolocalelowercase-tr-locale-scule](records/javascript-tolocalelowercase-tr-locale-scule.yml) | JavaScript | bug | yes | fixed |
| [python-lower-dotted-i-cpython](records/python-lower-dotted-i-cpython.yml) | Python | by-design | no | by design |
| [php-mb-strtolower-dotted-i](records/php-mb-strtolower-dotted-i.yml) | PHP | by-design | no | by design |
| [rust-to-lowercase-dotted-i](records/rust-to-lowercase-dotted-i.yml) | Rust | by-design | no | won't fix |
| [python-casefold-dotted-i-notebooklm-py](records/python-casefold-dotted-i-notebooklm-py.yml) | Python | expectation-gap | no | open |

## What a record looks like

```yaml
id: python-casefold-dotted-i-notebooklm-py
title: "Title lookup by casefold() cannot find \"İstanbul notları\" with the query \"istanbul\""
language: python
library: notebooklm-py
operation: casefold          # lower, upper, casefold, compare, regex-range, sort, slug, title-case, other
kind: expectation-gap        # bug, by-design, expectation-gap
letters: ["İ", "i"]          # which of I ı İ i
locale_dependent: false      # false = happens everywhere; true = only under tr_TR
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
  fix: "..."                 # which layer the approach uses
verification:
  status: verified           # a person or a named AI tool ran the command and saw `actual`
  by: "claude-code (AI), reviewed by halilunay"
  date: 2026-10-12
```

Full rules: [`schema/record.schema.json`](schema/record.schema.json). All records: [`records/`](records/).

## Add a record (about 10 minutes)

1. Copy [`records/_template.yml`](records/_template.yml) to `records/<language>-<operation-or-api>-<project>.yml`.
2. Fill the fields. The upstream link is required: an issue, PR, commit or bug-tracker page. Before calling something a `bug`, check what the standard and the project's own docs say.
3. Run the reproduction if you can (or have an AI tool run it and name it) and set `verification.status: verified` with `verification.by` saying who ran it; otherwise `unverified` with a note.
4. Open a pull request. CI runs `scripts/validate.py`; a maintainer checks the link and merges.

Details and the review checklist: [CONTRIBUTING.md](CONTRIBUTING.md). Have a case but no time for a PR? Open an issue with the [new record template](.github/ISSUE_TEMPLATE/new-record.md).

## Use the catalog in your tests

Each record's `input`/`expected`/`actual` is a test case; `reproduction.command` is the oracle. A ten-line runner in your language that loads `records/*.yml`, filters by `language` and asserts your own function on `input` is the intended use. Runners for popular languages are a welcome contribution (label `runner`).

## Sources

- Unicode Character Database 18.0.0: [`CaseFolding.txt`](https://www.unicode.org/Public/UCD/latest/ucd/CaseFolding.txt), [`SpecialCasing.txt`](https://www.unicode.org/Public/UCD/latest/ucd/SpecialCasing.txt), [`UnicodeData.txt`](https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt)
- The Unicode Standard 18.0.0, [§3.13 Default Case Algorithms](https://www.unicode.org/versions/Unicode18.0.0/core-spec/chapter-3/) (tailoring, D145 canonical caseless match)
- W3C, [Character Model for the World Wide Web: String Matching](https://www.w3.org/TR/charmod-norm/) (First Public Working Draft, 2026)
- Background: [Dotted and dotless I in computing](https://en.wikipedia.org/wiki/Dotted_and_dotless_I_in_computing)

## License

MIT. See [LICENSE](LICENSE).

---

## Türkçe

**Türkçenin dört "i"si (I, ı, İ, i) yüzünden kodun ya da kullanıcı beklentisinin bozulduğu gerçek vakalar: her kayıtta kopyala-yapıştır yeniden üretim, upstream bağlantısı ve uygun yaklaşım.**

Bu bir kütüphane değil, veri: her vaka bir YAML dosyası, hepsi CI'da denetleniyor, her dosya vakanın gerçekten olduğunu gösteren issue, PR ya da commit'e bağlı.

**Unicode `İ`'nin küçük harfi için üç uyumlu sonuç tanımlar:** basit eşleme `i` (Go, Java'nın karakter düzeyi; Java `String.toLowerCase` tam eşleme kullanır), tam eşleme `i` + U+0307 (Python, JavaScript, Rust, PHP, Ruby), Türkçe kural (`tr`, `az`) `i` ve `I` → `ı` (JS `toLocaleLowerCase('tr')`, Ruby `downcase(:turkic)`, ICU). Üçü de standarda uygun; sorun kodun bunları karıştırmasından çıkar.

**Üç tür kayıt (`kind`):**
- `bug`: kod standardı ya da kendi niyetini bozmuş, upstream düzeltmiş ya da kabul etmiş. Tipik örnek: `tr_TR` altında makine metni (ayar anahtarı, enum, SQL tanımlayıcı) `ı` alır. Yaklaşım: `Locale.ROOT`, `LC_ALL=C`, tanımlayıcıda `toLowerCase()`.
- `by-design`: çalışma ortamı Unicode varsayılanını doğru uyguluyor. Türkçe metin için Türkçe kurallı çağrı kullanılır (ICU, `toLocaleLowerCase('tr')`, Ruby `:turkic`).
- `expectation-gap`: kod standarda uyuyor ama kullanıcı arama tarzı eşleşme bekliyor (`istanbul` → `İstanbul`). Bu bir tasarım kararıdır. Önce normalleştir ve katla (NFD → casefold → NFC); gerekiyorsa aksan duyarsız ikinci kademe ekle (dikkat: `şık` = `sık` olur); `IĞDIR` = `ığdır` için yalnız Türkçe kural ya da `tr` karşılaştırıcı işe yarar.

`i`'den sonra U+0307'yi atmak `İ` için basit eşlemeyle aynı sonucu verir; yanlış değil ama Türkçe kuralın yalnız yarısıdır.

**Kayıt eklemek (yaklaşık 10 dakika):** `records/_template.yml` dosyasını `records/<dil>-<işlem>-<proje>.yml` adıyla kopyala, alanları doldur (upstream bağlantısı zorunlu; bir şeye `bug` demeden önce standarda ve projenin belgesine bak), yeniden üretimi bir kişi ya da adını yazdığın bir yapay zekâ aracı koştuysa `verified` yaz ve kimin koştuğunu `verification.by` alanına ekle, koşulamadıysa `unverified` + not; PR aç. Ayrıntı: [CONTRIBUTING.md](CONTRIBUTING.md).

Lisans: MIT.
