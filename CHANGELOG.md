## [0.10.1](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.10.0...v0.10.1) (2026-01-03)


### Bug Fixes

* Update issue URL format in multiple backends to match Slack backend structure ([22a4634](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/22a4634867ab93b13a5f214c5c4ff7279ad73fe4))

# [0.10.0](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.9.1...v0.10.0) (2026-01-03)


### Features

* Add Bugsink issue URL to alerts in various backends ([b21d207](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/b21d207c438b8264850b383791cf3b3382e3931c))

## [0.9.1](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.9.0...v0.9.1) (2026-01-03)


### Bug Fixes

* Prevent changing backend type for existing messaging services ([fccec0b](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/fccec0be1fba1922c3a2f96e8280773e2e1f6fef))

# [0.9.0](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.8.3...v0.9.0) (2026-01-03)


### Features

* Add 'Only New Issues' option to GitHub and Jira backends to prevent duplicates ([74acacc](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/74acacc11926c917605d227d61a019080c19e499))

## [0.8.3](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.8.2...v0.8.3) (2026-01-03)


### Bug Fixes

* Improve JavaScript injection logic to replace only the last endblock in template ([9628b56](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/9628b56c496779d4c2bf31a087f5fea66b9f642b))

## [0.8.2](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.8.1...v0.8.2) (2026-01-03)


### Bug Fixes

* Dynamically set initial kind for MessagingServiceConfigForm in project messaging service ([4130a2a](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/4130a2af1ce9d4bea79b81ad5cffa6d16873a075))

## [0.8.1](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.8.0...v0.8.1) (2026-01-03)


### Bug Fixes

* Update Microsoft Teams integration documentation for webhook configuration ([55a3658](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/55a3658650fb3beccfd26bce063fb0d40c97b679))

# [0.8.0](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.7.1...v0.8.0) (2026-01-03)


### Features

* Implement dynamic backend configuration and patching for Bugsink ([9a172c5](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/9a172c5261b159c97f7b57075028ddd64531dfe9))

## [0.7.1](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.7.0...v0.7.1) (2026-01-03)


### Bug Fixes

* Simplify backend file copying in Dockerfile ([e40b471](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/e40b4715998c099c976dea052463946806e1f28c))

# [0.7.0](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.6.0...v0.7.0) (2026-01-03)


### Features

* Add support for new messaging backends: Microsoft Teams, PagerDuty, and Generic Webhook ([587db4e](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/587db4ef5708d1fa0b33b3a09d30fb4cc3018572))

# [0.6.0](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.5.0...v0.6.0) (2026-01-03)


### Bug Fixes

* Add debug output for backend registration process in Dockerfile and register_backends.py ([d776f8a](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/d776f8a92177ced2ac356b1cff28e3f89e4b2dea))
* Remove debug output from Dockerfile for cleaner build process ([27bc782](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/27bc7828c5c77b176221f1b250fe1a1e65f691b3))
* Switch to root user for modifying site-packages in Dockerfile ([00d26f2](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/00d26f2ec6d8edd105d2d5e822ed104b54652ecb))


### Features

* Update backend registration and configuration for Jira Cloud and GitHub Issues ([e073a55](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/e073a55931ffcac198ed92105aaad5ab599558bf))

# [0.5.0](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.4.0...v0.5.0) (2026-01-03)


### Features

* Implement custom messaging backends for Jira Cloud and GitHub Issues ([0483dfb](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/0483dfbf650784201b7e6c0a2e74def6be9c838d))
* Set default initial values for repository and labels in GitHub Issues configuration form ([1f1ce9c](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/1f1ce9ccf15a5e2b9d26a52ce6a3dfd0ac93b786))

# [0.4.0](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.3.0...v0.4.0) (2026-01-03)


### Features

* Add remote installer scripts for Client-Kit in PowerShell and Bash ([3ea2b51](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/3ea2b51d423392a934196949c8caf982601bc104))
* Implement API mode for automatic project and team creation in Client-Kit ([80716a1](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/80716a120b9767a2fe881356152703ceac06de38))

# [0.3.0](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.2.0...v0.3.0) (2026-01-03)


### Features

* Add cross-platform installer for Sentry SDK integration ([46d01de](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/46d01dea76689b596f6b57fd293b816d3787946e))

# [0.2.0](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.1.2...v0.2.0) (2026-01-03)


### Features

* Add comprehensive Bugsink/Sentry SDK integration examples for Rust and TypeScript ([c1211fa](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/c1211fa3735e01ca2769217e3d7acceb25d17ffb))

## [0.1.2](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.1.1...v0.1.2) (2026-01-03)


### Bug Fixes

* Update ALLOWED_HOSTS to include IPv6 localhost address ([f514c72](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/f514c72d5e176d74f5e92fc24863e99611941222))

## [0.1.1](https://github.com/bauer-group/CS-ApplicationErrorObservability/compare/v0.1.0...v0.1.1) (2026-01-03)


### Bug Fixes

* Add ALLOWED_HOSTS environment variable for improved host configuration ([5797a48](https://github.com/bauer-group/CS-ApplicationErrorObservability/commit/5797a488f14fda265d34b1cc4f1353ce77877f95))

# [0.1.0](https://github.com/bauer-group/CS-ErrorObservability/compare/v0.0.0...v0.1.0) (2026-01-03)


### Bug Fixes

* Correct port configuration placement in docker-compose for server exposure ([6c995d8](https://github.com/bauer-group/CS-ErrorObservability/commit/6c995d8bf8c3c1800717ed99eebdad7965b83704))
* Inital Release Flow ([5dc35da](https://github.com/bauer-group/CS-ErrorObservability/commit/5dc35da903093ed5a3dfa9e6d20f823d97160a82))
* Refactor code structure for improved readability and maintainability ([a08529d](https://github.com/bauer-group/CS-ErrorObservability/commit/a08529de92f169e7757fb273519f94f9d720c6dc))
* Update configuration and improve Docker scripts for Error Observability tools ([6906f82](https://github.com/bauer-group/CS-ErrorObservability/commit/6906f8244b2ad9fb6a31a457512667e5a49d2d12))


### Features

* Add development settings for local server port in .env.example ([0297342](https://github.com/bauer-group/CS-ErrorObservability/commit/0297342eb9b3c1bf09e30115507378e5ee261b93))
* Implement scripts for generating secrets and managing Docker container for Error Observability setup ([a41c451](https://github.com/bauer-group/CS-ErrorObservability/commit/a41c451e5df317c51b1464c0ae098d7be3596e2f))
* Pre Release Implementation ([0465cdc](https://github.com/bauer-group/CS-ErrorObservability/commit/0465cdc7286e9ae10a0666974f619d6726eca154))
* Update Docker configurations and add comprehensive README for Error Observability setup ([a36cfff](https://github.com/bauer-group/CS-ErrorObservability/commit/a36cfff0b6b7324b10479102c8cdc252ffa46879))
