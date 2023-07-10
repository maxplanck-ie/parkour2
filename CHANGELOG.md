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
