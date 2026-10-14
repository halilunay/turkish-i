# Contributing

Thanks for adding to the catalog. One record is a real contribution; you do not need to add more than one.

[Türkçe özet aşağıda](#türkçe-özet)

## What counts as a record

- A **real** case: it happened in a real project and there is a public link (issue, pull request, commit, bug tracker page) that shows it. "I think this could break" is not a record.
- Caused by the Turkish letters **I, ı, İ, i** (case conversion, comparison, regex ranges, sorting, slugs, title case).
- Not already in `records/`. Same mechanism in a different project is fine (we want to know *where* it bites); the same upstream link twice is not.

Set `kind` honestly (see the README): `bug` only when the code broke the standard or its own intent and upstream fixed or confirmed it; `by-design` when a runtime correctly applies a Unicode default mapping (Python, PHP, Rust closed these as "by design" or "won't fix", and people still need the right approach); `expectation-gap` when the code follows the standard but users expect search-style or Turkish-aware matching. Before calling something a bug, read what the Unicode data files and the project's own docs say.

## Steps

1. Copy `records/_template.yml` to `records/<language>-<operation-or-api>-<project>.yml`. The file name must equal the `id` field. Examples: `python-casefold-dotted-i-notebooklm-py`, `bash-grep-bracket-range-tr-locale-gstack`.
2. Fill every field. Keep `title`, `input`, `expected`, `actual` short and literal; put the explanation in `actual` or `verification.notes`.
3. `reproduction.command`: the smallest copy-paste command that shows the bug, ideally against the language runtime alone. Add the observed output as a comment line. Say what you ran it on in `environment`.
4. Run it if you can. `verification.status: verified` means someone, you or an AI tool you name, actually ran the command and saw `actual`. Put who ran it in `verification.by`: your GitHub login, or `<tool> (AI), reviewed by <your-login>` if an AI tool ran it. If nobody could run it (no Windows, no tr_TR locale, no JVM), write `unverified` and say why in `notes`; a maintainer or another contributor can verify later.
5. Check locally (optional, CI does it too):

   ```sh
   pip install pyyaml
   python3 scripts/validate.py
   ```

6. Open a pull request. One record per PR keeps review fast.

## Review checklist (what the maintainer looks at)

- Link opens and shows the case described.
- `expected` and `actual` differ and are literal (hex or `\u` escapes welcome when the glyphs look alike).
- `locale_dependent` is right: `true` only if the case needs a Turkish locale to appear.
- `kind` is right, and `expected` is backed by the standard, the project's docs or the upstream discussion, not only by intuition.
- `upstream.fix` names the layer it uses (simple or full mapping, Turkish tailoring, normalization, `Locale.ROOT`).
- `letters` lists the letters actually involved.
- `upstream.status` matches the link today.

## Labels

- `good first issue`: a record we know about but have not written; the issue has the link, you write the file.
- `needs-verification`: an `unverified` record; run the command on your machine and open a PR flipping it to `verified`.
- `runner`: a small script in some language that loads `records/*.yml` and asserts a function against them.
- `new-record`: issues opened with the record template, waiting for a file.

## AI assistance

Records written or verified with help from an AI tool are fine. Say so in one line in the PR description. The reproduction must really have been run, by a person or by an AI tool you declare, and it is named in `verification.by` (for example `claude-code (AI), reviewed by your-login`). The person who submits the record vouches for the result: you have read the output and you stand behind it.

## Conduct

Be kind, be literal, link your sources. Disagreements about what Unicode "should" do go upstream, not here; here we record what happened.

---

## Türkçe özet

- Kayıt = gerçek bir vaka + herkese açık kanıt bağlantısı (issue, PR, commit). "Bence bozulur" kayıt değildir.
- `kind` dürüst seçilir: `bug` yalnız kod standardı ya da kendi niyetini bozduysa; `by-design` çalışma ortamı Unicode varsayılanını doğru uyguluyorsa; `expectation-gap` kullanıcı arama tarzı ya da Türkçe duyarlı eşleşme bekliyorsa. "Hata" demeden önce Unicode veri dosyalarına ve projenin belgesine bakılır.
- `records/_template.yml` dosyasını `records/<dil>-<işlem>-<proje>.yml` adıyla kopyala; dosya adı `id` ile aynı olmalı.
- Yeniden üretim komutunu bir kişi ya da adını yazdığın bir yapay zekâ aracı gerçekten koştuysa `verified`, kimse koşamadıysa `unverified` + neden. Kimin koştuğu `verification.by` alanına yazılır: GitHub adın ya da `<araç> (AI), reviewed by <adın>`.
- Yerelde `pip install pyyaml && python3 scripts/validate.py`; CI de aynı şeyi çalıştırır.
- PR başına bir kayıt. Yapay zekâ yardımı aldıysan PR metninde tek satırla söyle. Yeniden üretimi bir kişi ya da beyan edilmiş bir yapay zekâ aracı gerçekten koşmuş olmalı; kaydı gönderen kişi sonuca kefil olur (çıktıyı okudu, arkasında durur) ve aracı `by` alanında yazar.
- Etiketler: `good first issue` (bağlantı hazır, dosyayı sen yaz), `needs-verification` (komutu kendi makinende koş), `runner` (dilinde 10 satırlık koşucu), `new-record` (şablonla açılmış issue).
