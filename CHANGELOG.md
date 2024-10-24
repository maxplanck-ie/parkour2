> Versioning is by dates (in `yy.mm.dd` format).

??.??.??
========

- **We're now running on Python 3.12** (its CI jobs were reintroduced), and we have also added support for Python 3.13.
- We have switched over to `uv` everywhere (Makefile, Docker, CI) instead of plain `pip-tools`.
- Replaced `isort` and `black` with `ruff` (CI).
- Added history tracking to the `Duty` model.
- Added a 'Get Flowcell' context menu for staff users to find where each sample is being sequenced.
- Fixed a bunch of typos.
- ...


24.10.18
========

- E-mail communications: grayed-out "send" button after 1 click, to avoid spamming inboxes.
- Fixtures: `save_initial_data` management command will now be using the built-in json formatter instead of `jq`.
- Updated clipboard functionality at Incoming submodule.
- Updated organisms names on both production database and fixtures.
- Updated dependencies.


24.08.20
========

Breaking changes:

- Temporarily dropped CI tests for Python 3.12, which were [broken via Numpy dependency](https://numpy.org/doc/stable//release/1.26.0-notes.html)). We're using Python 3.11 since Parkour2 version 0.3.9 anyway. We'll catch-up to Python 3.12 once the situation stabilizes and other projects are successful sailing through this difficulty... For now, our `requirements.txt` environment is unable to resolve under 3.12

Non-breaking changes:

- Fixed a bug that made flowcells on the last day of the month not to be listed under Load FCs or Invoicing. Now, we are only blind over the last minute of the last day of the month.
- New retrieve_samplesheet API endpoint under flowcells. By default, it gets you the XLSX samplesheet containing all lanes of a flowcell. For example, `<URL>/api/flowcells/retrieve_samplesheet/?flowcell_id=...`
- Dropped pip cache (experimental Dockerfile syntax) to avoid obscure error messages. We are dealing with these (and other pkg caches) by using a cronjob that runs the build in the VMs.


24.07.24
========

- Index Generator was adjusted to work coherently with Samples that were coming back after 'Destroy Pool' (indexes are fixed, as Libraries.)
- Fix crash (FPDFUnicodeEncodingException) when user tries downloading the Request signature form with non-UTF8 characters in the Description.
- Dev deployments now have an integrated tool available for generating, saving, and running SQL queries: [SQL Explorer](https://www.sqlexplorer.io)  (use: `make enable-explorer` to activate, and then navigate to `<URL>/explorer`.)
- Updated all of our Python package dependencies.


24.06.28
========

- 'Destroy Pool' option when right-clicked on pools, in the 'Pooling' submodule. (#109)
- New search bar component in the 'Libraries & Samples' submodule, which searches either by pressing enter or clicking the search button. (#110)
- Logout method changed from GET to POST to make it compatible with Django v5.0. (#111)
- Fixed: "Bad Request" notification after adding Libraries or Samples while creating any request and the description is kept empty. (#112)
- Option to select OS under "File Paths" to modify the file paths according to the selection. (#113)
- Feature to add paths from the user's end, via "User Paths" in File Path right-click option. (#117)


24.05.10
========

- Example XLSX file for import index plate pairs is columwise now.
- Description is no longer required for adding libraries and samples in the 'New Request' window. (#106)
- Added (*) to the Description label in 'New Request' window. (#106)
- Set the default value to 1 to create empty records in 'Add Libraries' window. (#106)
- Changed the color of link 'Max page on Intranet' from Golden to White in 'Add Libraries' window. (#106)
- In 'Add Libraries' window, fixed the 'Sequencing Depth' validation error popping up while editing. (#106)
- In 'Add Libraries' window, fixed the 'Size (bp)' column always has a default value of 0 whenever an empty record is created. (#106)
- In 'Add Libraries' window, renamed 'size (bp)' to 'Size (bp)'. (#106)
- Changed the naming format of Benchtop Protocol File in 'Library Preparation' and 'Pooling' to have the 'Request IDs' and 'Pool ID' in front. (#105)
- New Benchtop Protocol File in 'Pooling' with the introduction of 'Smear Analysis' (#107)


24.03.27
========

- Renamed 'Nucleic Acid Type' to 'Input Type', to accommodate the latest type addition ('Cells').
- In 'Invoicing', Download Report, Upload Reports, and View Uploaded Reports buttons are functional again. (#101)
- Standardized date parameter format to "YYYY-MM" in 'Invoicing' and 'Load Flowcells' submodule. (#101)
- While downloading, renamed the Benchtop Protocol File in 'Library Preparation' and 'Pooling' to have the 'Request IDs' and 'Pool ID' respectively. (#102)
- BugFix: Fixed various costs in 'Invoicing' appear as 0. (#103)


24.03.15
========

- Added date-range picker in 'Invoicing' submodule. (#99)
- Fix to PI accounts being unable to access all corresponding media files.
- Allow lengthier indeces' name or prefixes.
- BugFix: "Delivered" status has now a green-colored circle at 'Libraries & Samples' app submodule. (#100)
- Rephrased text in email sent after Electronic Approval.
- Added Seq. Length and Depth to Electronic Approval. Old PDF was not updated (yet) because of reasons.


24.02.20
========

- Added date-range picker in 'Load Flowcells' submodule. (#96)
- Added a library protocol filter, and added pool into search functionality, for 'Libraries & Samples' staff UI. (#95)
- Fixed a misconfiguration with Django that interfered with the URL shared to PIs for Paperless/ Electronic Approval of sequencing requests. (`7a85900`)
- new URL: `/api_user_details` (not really an api endpoint), gives some basic user data to upcoming frontend (VueJS).
- new URL: `/danke` (users are redirected after seq. request approval)
- new nucleic acid and library protocol types for single cell sequencing.
- `put-old-migras` and `sweep` rules are more robust now.


24.01.31
========

Breaking changes:

- Dropped support for Python 3.9 (no more CI tests, which were [broken via dependencies](https://github.com/maxplanck-ie/parkour2/actions/runs/7543943036/job/20536098669#step:8:99)). We're using Python 3.11 since Parkour2 version 0.3.9 anyway.
- Enabled pre-commit hook to run a new linter (prettier).

Non-breaking changes:

- Added a statuses filter and search functionality for 'Libraries & Samples' staff UI. (#93)
- Added support for Python 3.12 (CI tests are passing), consider this experimental.
- Upgraded Python dependencies.
- Hidden Print button from Usage charts, since it was redirecting to a different site. (#90)
- Request model has a new JSONfield, `metapaths`. It's meant to be like filepaths, but editable by users and the strings most probably refer to URLs (e.g. eLabJournal).
- Added a 'Solicit approval via e-mail' context menu option for sequencing requests that belong users with both their own and their PI's email address at same server as the admin (`settings.SERVER_EMAIL`). Such PIs doesn't need an account on the system, the link is open to everyone. That's why we are logging some metadata from the HTTP request.
- Playwright tests for the new frontend, Vue.js for Duties. (#86)
- Added new option "Short + Long" to the Platform field for Duties. (#89)
- Minor cosmetic changes, and a new search bar for Libraries and Samples. (#87)


23.11.22
========

- Updated all dependencies.
- Subfolders were re-arranged. Basically, the old frontend (ExtJS), its tests (playwright), and the Django Project (`./parkour_app`) are now under `./backend`. Meanwhile, there's a new frontend under development, using ViteJS; and it's under `./frontend` subfolder. Also, there's a new Dockerfile, and container, for it.
- A new column (`Pool Paths`) was added to the 'Libraries and Samples' section of the app, to easily find where each sample (or lib) was loaded.
- Staff users will find a new calendar icon that takes them to 'Duties', our first module using the new VueJS framework. Over there, we'll be keeping track of our rotations as to who is responsible of what (e.g. X person from Bioinformatics Facility is in charge of processing the short-read sequence data for ~3 months).


23.11.02
========

Breaking changes:

- `<URL>/api/requests/<id>/get_email/` was renamed to `get_contact_details`, and the JSON Response now includes more data from the user.
- Removed the \[broken\] import and export functionality at IndexPairs. Instead, we have a custom bulk import button now that works exclusively with plate coordinates. This may be a temporal solution until we work out the rough edges with the extension custom import (foreingkeywidget)
- Removed `DJANGO_SETTINGS_MODULE` from `misc/parkour.env`, given that it's implemented as part of the Docker build stages. To be clear, if you don't remove it there, the hardcoded value will overrule over the docker-compose switch that we are using for makefile rules `dev`, etc.
- Breaking changes for backup locations! `./rsnapshot` was moved under `./misc`, so the config files will be there.. that's not much of an issue. Yet, the backups subfolder (or symlink) will need to be adjusted manually.
- `/media_dump` is no longer a symbolic link. ~~We're now actually using it for each update (the docker volume recycling trick we were relying on stopped working in latest docker versions).~~ EDIT: seems like it does work, but we're keeping this change; at least for now.

Non-breaking changes:

- **Updated our core dependency**, Django, to version 4.2 (LTS). The previous LTS release 3.2 reached end of extended support in April. We thank the Django core team that kept releasing security fixes even after.
- New dependency added, navigate to `<URL>/openapi/schema/redoc` or `<URL>/openapi/schema/swagger-ui` to enjoy either ReDoc or Swagger UI over the automagically generated OpenAPI 3.0 schema.
- New dependency added, navigate to `<URL>/schema-viewer` to enjoy it (installed on dev settings only). Remember: use `models` rule if you'd like to have these in static print-friendly PDF docs.
- Added a new Django management command: list_templates
- Added `filepaths` JSONField to Request model. We'd like to track the location of, for example, delivered FASTQ files and QC reports.
- Deprecated and removed bpython. shell_plus now uses ipython. This was to avoid runtime errors while compiling the requirements.txt files, given that greenlet dependency would be pinned under contradicted version numbers (testing.txt has playwright that asks for greenlet v2, meanwhile bpython in dev.txt asked for v3..)
- Email address displayed next to User (its string representation) now skips the email host if it's the same as in EMAIL_HOST settings (parkour.env) and instead displays `<user>@~`.
- Added Phone next to email address for User display (if available).
- Added 'archival' feature to CostUnit(s).
- Renamed rules `import-migras` to `put-old-migras`, `export-migras` to `tar-old-migras`, and `restore-migras` to `put-new-migras`. This is to avoid confusion with `import-pgdb`, where importing means bringing file from prod VM.
- Rule `import-pgdb` now brings migration files (to reproduce database schema) by default (if available).
- The `<URL>/api/samples/<id>` doesn't fail anymore if no `pk` was given.
- Added an EmailField to PrincipalInvestigator. This field is going to be used in the 'paperless approval' feature (see next release.)
- Added new endpoint, `<URL>/api/requests/<id>/get_poolpaths/`, returns a dictionary with records' barcode as keys and pool names as values, to easily find where each sample (or lib) was loaded.


23.09.20
========

- New rule `db-migras`: loads production database snapshot with a proper reset of migration files. See source code and its help message for instructions on how to use it. It is a drop-in replacement to `db` rule when development version moved forward with changes into Django models that are not synchronized (yet) with production deployment that shall always run a version following github releases.
- New 'Duties' model, to keep track in charge of whom are the responsibilities (both dry and wet processing of both short and long read sequencing.); so far it lists all users in database, but it's meant to be used only within the sequencing facility, and bioinformaticians.
- New 'archived' field replaces the old obsolescence functionality that was broken in many if not all models. By default, all archived instances of models are filtered out at the Site Admin panel.
- BUGFIX: Uploaded files appeared and disappeared just by switching sequenced to True.
- BUGFIX: One API endpoint (`/api/samples/?request_id=nnnn`) was giving error 400 to non-staff users.
- Renamed `parkour_app/migrations` to `parkour_app/extras` to avoid confusion with actual migrations. Renamed the corresponding `test.py` in there to `test_migrations.py` accordingly.
- Added user email to mailed traceback when Django encounters any errors. This way we can contact users if they were experiencing a bug.
- Added database from parkour-demo in JSON format under `misc/` subfolder. Integrated all `**/fixtures/*.json` into it.
- Updated fixtures with parkour-demo database, useful to overwrite or further customize such entries.
- Restored old makefile rules to save or load database in json. Do not use them with production data, BarcodeCounter bug is still in place, and it will be reset to 0 every time you use the json format. These rules are only meant to be helpers for the demo data which we prefer to have in JSON so that it's more robust to models' migrations.
- Added `tblib` as a base dependency to have proper traceback when running tests in parallel.
- Improvement: sweep rule won't remove current symlink targets anymore.


23.08.21
========

- BUGFIX: the rule `load-fixtures` was missing the pre-requisite rule `apply-migrations` (#59)
- BUGFIX: password reset was redirecting to a missing success URL (giving a 404 to users right after resetting their passwords, what seemed misleading). We now redirect to login.
- IMPROVEMENT: Django Linear Migrations extension moved from `dev.py` to `base.py` settings. This way we are ready to run `makemigrations` in any deployment (Be it production or development.)


23.08.17
========

**Full commit history**: https://github.com/maxplanck-ie/parkour2/compare/0.3.9...23.08.17

## Important News

- We abandoned semantic versioning, from now on we will use dates. This is displayed on the `login.html`, right above where users input their credentials.

- `parkour.env.sample` has a new environmental variable (`CSRF_TRUSTED_ORIGINS`) that requires manual intervention/ copy to your deployments configuration. This way we are prepared for upcoming Django 4.2

- Ever since our pre-relased 0.3.9 version, some seemingly redundant files corresponding to our frontend were removed. **We did our best to fix any issues in this release**. Yet, if you see a blank page on a fresh installation, please check the browser console (e.g. pressing F12) and [file a new issue](https://github.com/maxplanck-ie/parkour2/issues/new) with the corresponding log message (e.g. pressing F12 and looking for the 'could not load **.js' or 'file not found' error messages.)

## Dependencies

- Updated all python requirements, but keeping on Django 3.2 to avoid an ongoing issue with sequencing depth miscalculation.
- **New CSRF_TRUSTED_ORIGINS option in `misc/parkour.env`**, lists domains were application is deployed. You may use a wildcard to trust all subdomains. Be sure to add it, as in the file we provide: `misc/parkour.env.sample`. This will be mandatory once we update to Django 4.2
- The docker image is now using Debian Bullseye as base, to match [playwright system requirements](https://playwright.dev/python/docs/intro#system-requirements).

## Bugfix

- Failed sequencing are now skipped from invoice XLS report. In the past staff users (sequencign team) needed to go request by request un-checking the 'sequenced' status on each.

## Testing

- **new rules: coverage-html coverage-xml**, run pytest with code coverage report(s).
- **new rule: playwright**, to run end-to-end tests (frontend), for now 2 test were implemented.
- The old test rule is now renamed as **djtest**, and it only runs the django unittests (functional + integration).
- added django-linear-migrations extension, to ease up fixing merge conflicts if we were to change models on different git branches.
- added django-migration-linter with a **new rule**: lint-migras. This is now part of the **test rule** too, even though it's failing for 25 out of 38 migrations (see: [incompatibilities](https://github.com/3YOURMIND/django-migration-linter/blob/main/docs/incompatibilities.md) for details, we have plenty of altering columns and a couple of missing default values on DB schema..)
- Removed old debugging strategy of attaching term to docker container to work with PDB. It was too clunky, and we've been using werkzeug traceback interpreter anywayz.

## Improvements

- New permission for users: 'Access as PI', grants them the ability to see all requests shared under their PrincipalInvestigator, whichever that is.
- **new rule: reload-code**, sends the hung-up signal to green unicorn, gracefully reloading the wsgi config and the app code (details [here](https://docs.gunicorn.org/en/latest/signals.html#reload-the-configuration)) (note: development deployments run on werkzeug and auto-reload code via the docker bind mounts anyway!)
- Fixtures (JSON) are in long format now, and a new django-admin custom command `save_initial_data` is available to share some of our data to other research facilities. The good old `load_initial_data` is there too.
- Backup cronjobs are more separated in time now, to avoid [a known issue](https://serverfault.com/a/221646) with `rsnapshot`.
- rule `models` now generates 3 PDF files, one is a simple A4 sheet for quick preview, and the other two are for printing posters in A1 size using multiple sheets in either A4 or A3 sizes.
- Support for developers working on Windows is better now. Feel free to open an issue if you face further difficulties.

## Changes

- Submission of sample and libraries updated, we are hardcoding values for columns that are now hidden in frontend (e.g. concentration_method and RQN). Like always, custom parameters and its values can be passed in the free-text form inside Description or using file attachments to each request.


0.3.9
=====

**Full Changelog**: https://github.com/maxplanck-ie/parkour2/compare/0.3.8...0.3.9

- **Removed some redundant static files**[^1]. In case of any errors while updating UI or doing new deployments, developers are advised to go grab these from the previous release zip file.
- Updated dependencies
- Dropped support for Python 3.8 that reached end of life
- Upgraded to python 3.11, while maintaining support for 3.10 and 3.9 in our CI builds
- Moving away from pytz to the new lib under datetime module
- Tests now check for missing migrations. And they run in parallel
- Doubled the number of green unicorn workers
- Log messages are enriched now. Also, added delay option so that file opening is deferred until the first call to emit().
- Development deployments now have PYTHONDEVMODE enabled (e.g. expect to see warnings from underlying core dependencies, e.g. mixing django 4.2 with python 3.9)
- Updated link to readthedocs to our current wiki here on GitHub
- Added a visible link to MAX intranet so that users can see all documentation from the Deep Sequencing Facility when submitting new requests
- From now own, user request only accept Sequencing Depth values >= 10M. See our internal announcement for further details[^2].

---

[^1]: A new UI, with a modern JS framework, is in the works...

[^2]: Before, we only recommended 10 million reads per sample as a minimum, but did not restrict entries in Parkour. Background is that we use large scale analyzers to sequence samples. For technical reasons, the lower the sequencing depth per sample, the more difficult it is to accurately reach the sequencing depth ordered. Hence, quite some outliers will be produced. Please note: The overall read quality is not affected by shallow sequencing. Most of our requests will be unaffected by this change, since a transcriptome or genome typically requires a much deeper sequencing per sample (30M, 50M etc.). - Users that used sequencing depth below 10M on the NovaSeq, we kindly ask you to try this new system to hopefully avoid discussions on differences in reads requested and reads delivered ("I ordered 3M reads but got only 0.7"). It can still happen that sequencing depth is off. As usual, we will investigate and re-sequence if needed. - Miseq Users: we understand that this new regulation is not helpful for MiSeq requests. The MiSeq is hardly in use, and we ask you to use the comment field in Parkour to additionally specify depth per sample. Thanks for your comprehension.
