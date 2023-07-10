0.4.0
=====

**Full Changelog**: https://github.com/maxplanck-ie/parkour2/compare/0.3.9...0.4.0

> **IMPORTANT**: Since we've upgraded the backend (Django), `parkour.env.sample` has a new environmental variable (`CSRF_TRUSTED_ORIGINS`) that requires manual intervention/ copy to your deployments configuration.

> **NOTICE**: Ever since our pre-relased 0.3.9 version, some seemingly redundant files corresponding to our frontend were removed. **We did our best to fix any issues in this release**. Yet, if you see a blank page on a fresh installation, please check the browser console (e.g. pressing F12) and [file a new issue](https://github.com/maxplanck-ie/parkour2/issues/new) with the corresponding log message (e.g. pressing F12 and looking for the 'could not load **.js' or 'file not found' error messages.)

## Dependencies

- Updated all python requirements, including our core dependency: **Django, to version 4.2 (LTS)**. The previous 3.2 reached end of extended support in April, although Django core team kept releasing security fixes (thanks!)
- **New CSRF_TRUSTED_ORIGINS option in `misc/parkour.env`**, lists domains were application is deployed. You may use a wildcard to trust all subdomains. Be sure to add it, as in the file we provide: `misc/parkour.env.sample`.

## Bugfix

- Failed sequencing are now skipped from invoice XLS report. In the past staff users (sequencign team) needed to go request by request un-checking the 'sequenced' status on each.

## Testing

- **new rule: pytest**, to run tests with pytest (soon we'll add playwright end-to-end tests)
- added django-linear-migrations to development, to ease up fixing merge conflicts if we were to change models on different git branches.
- added django-migration-linter with a **new rule**: lint-migras. This is now part of the **test rule** too, even though it's failing for 25 out of 38 migrations (see: [incompatibilities](https://github.com/3YOURMIND/django-migration-linter/blob/main/docs/incompatibilities.md) for details, we have plenty of altering columns and a couple of missing default values on DB schema..)
- The old test rule is now renamed as **djtest rule**, and it only runs the django unittests (functinal + integration).
- Removed old debugging strategy, we've been using werkzeug traceback interpreter anyway.
- **new rule: coverage**, run pytest with code coverage report(s)

## Improvements

- **new rule: reload-code**, sends the hung-up signal to green unicorn, gracefully reloading the wsgi config and the app code (details [here](https://docs.gunicorn.org/en/latest/signals.html#reload-the-configuration))
- Backup cronjobs are more separated in time now, to avoid [a known issue](https://serverfault.com/a/221646) with `rsnapshot`.


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
