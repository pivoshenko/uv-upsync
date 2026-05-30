# CHANGELOG

<!-- version list -->

## v2.4.0 (2026-05-30)

### Bug Fixes

- Replace singleton metaclass with __new__-based singleton
  ([`53b7737`](https://github.com/pivoshenko/uv-upsync/commit/53b77372e484a3695f5bbac0cb4abfaf58821a39))

- **ci**: Configure ty python-version to match ruff target
  ([`1cc34f1`](https://github.com/pivoshenko/uv-upsync/commit/1cc34f10645df6885c484aeb844d9cf25defdace))

### Build System

- Bump pytest to 9.0.3 to fix GHSA-6w46-j5rx-g56g
  ([`4479cf6`](https://github.com/pivoshenko/uv-upsync/commit/4479cf679006e7fd3224221441dc70eb29e41865))

- Drop unused pytest-lazy-fixture (incompatible with pytest 9)
  ([`fe3176a`](https://github.com/pivoshenko/uv-upsync/commit/fe3176a69c5d86f67324fadd60500e6249dcc3b1))

- Update dev dependencies
  ([`b0813fa`](https://github.com/pivoshenko/uv-upsync/commit/b0813fa8191f364761833cb5f83c22fad71af146))

- Update dev dependencies
  ([`5ef0fe5`](https://github.com/pivoshenko/uv-upsync/commit/5ef0fe5b9eb2f7c77a5218c4a979667e7f9a5021))

- Update dev dependencies
  ([`dd39a19`](https://github.com/pivoshenko/uv-upsync/commit/dd39a191d129b9a712bb674b1b73a5630c997fc7))

- Update dev dependencies
  ([`dcd9ed7`](https://github.com/pivoshenko/uv-upsync/commit/dcd9ed7c4d66e55b714b00835030d81d9f8554b5))

- Update dev dependencies
  ([`2b8bb0b`](https://github.com/pivoshenko/uv-upsync/commit/2b8bb0bb732d7d8dd1b478e0db01a6e5055f94bf))

### Chores

- Align pyproject keywords with github repository topics
  ([`2f420db`](https://github.com/pivoshenko/uv-upsync/commit/2f420db49e3c0c4f4c4c3e8604eef2088026885f))

- Keep dependencies-upgrade and packaging-upgrade keywords
  ([`9140317`](https://github.com/pivoshenko/uv-upsync/commit/9140317c0bdcf042620338153547d925547d14ac))

### Documentation

- Clearer tagline
  ([`d445a73`](https://github.com/pivoshenko/uv-upsync/commit/d445a73bf570082606f3ba43100d1ddae170d775))

- Drop manual table of contents in favor of github's built-in
  ([`aa5c0a6`](https://github.com/pivoshenko/uv-upsync/commit/aa5c0a60fb2c7d27db40de3238a79a5cc452826e))

- Note that examples can be run with uvx without installing
  ([`a6c20a8`](https://github.com/pivoshenko/uv-upsync/commit/a6c20a8a7ec33e1872c5d4e801953a5a868bc4a7))

- Reorder badges, add table of contents, simplify overview
  ([`88b5592`](https://github.com/pivoshenko/uv-upsync/commit/88b55923883e530d11827e32243598bc8a85c100))

### Features

- Add --format json/markdown output and expose it from the action
  ([`618bb44`](https://github.com/pivoshenko/uv-upsync/commit/618bb44faf66554c4dce817f284ba096caf2a7d8))

- Add [tool.uv-upsync] config, pre-commit hook, and GitHub Action
  ([`9d718a9`](https://github.com/pivoshenko/uv-upsync/commit/9d718a9573cec997bb5826e2ea4c9c4cd747b075))

- Align uv-upsync with the uv ecosystem
  ([`3557c71`](https://github.com/pivoshenko/uv-upsync/commit/3557c71a9163f35abb57f25d7897ced593bdc888))

- Best-effort resolution that isolates un-lockable upgrades
  ([`2e5bfc8`](https://github.com/pivoshenko/uv-upsync/commit/2e5bfc8a68b1708c1339dfb08f88ead5f0fada72))

- Render failures as uv-style errors instead of tracebacks
  ([`7ad19d6`](https://github.com/pivoshenko/uv-upsync/commit/7ad19d6f07762385b5b8f834cd1e7623eb0e42fa))

- Resolver-aware --resolve, conflict naming, and a VHS demo
  ([`07ad6fd`](https://github.com/pivoshenko/uv-upsync/commit/07ad6fd3600d3836a4b484e7422de221eb2a9d31))

- Support compound ranges, --max-bump, and --prerelease
  ([`973e8fa`](https://github.com/pivoshenko/uv-upsync/commit/973e8fa351d743a7dd9c1d577fdd5dc835789445))


## v2.3.2 (2026-03-29)

### Chores

- Remove deprecated GitHub workflows and files
  ([`9f2f579`](https://github.com/pivoshenko/uv-upsync/commit/9f2f5795469ac2535bdaf12c938950588184a174))

### Documentation

- Remove TOC
  ([`91548dc`](https://github.com/pivoshenko/uv-upsync/commit/91548dc7d012087d2640ea6f7c6f68fcc294a160))


## v2.3.1 (2026-03-29)

### Build System

- Update dependencies
  ([`b7b8061`](https://github.com/pivoshenko/uv-upsync/commit/b7b806147b11da89976b39fc13fd239756c6542d))

### Documentation

- Update badge
  ([`15b9bf9`](https://github.com/pivoshenko/uv-upsync/commit/15b9bf9bc5b83504cb7a2d685af216dadf936f48))


## v2.3.0 (2026-03-29)

### Build System

- Update dependencies
  ([`041cc55`](https://github.com/pivoshenko/uv-upsync/commit/041cc551127d8228e351803daf9673b43a638a1a))

- Update dependencies
  ([`ca5c1c2`](https://github.com/pivoshenko/uv-upsync/commit/ca5c1c2904859ea6f860c27aa4713355093747ff))

- Update dev dependencies
  ([`5949e95`](https://github.com/pivoshenko/uv-upsync/commit/5949e957d7af4e1cf41ee6e44f1c1038914d71b6))

### Refactoring

- Run ty
  ([`9e7702b`](https://github.com/pivoshenko/uv-upsync/commit/9e7702b099f5ee11aa0838ca49b66ad91d4c850f))


## v2.2.0 (2026-03-08)

### Bug Fixes

- Update metadata
  ([`dd76201`](https://github.com/pivoshenko/uv-upsync/commit/dd76201fb5332f5fdb412e74b575f89e9e50e657))

### Build System

- Update dev dependencies
  ([`9cd1b8b`](https://github.com/pivoshenko/uv-upsync/commit/9cd1b8bf77d3c467db9f8adec7539db4b3600ce9))

- Update dev dependencies
  ([`12c5254`](https://github.com/pivoshenko/uv-upsync/commit/12c5254112e6e026cc6ee4691ea018d31229d4ac))

### Chores

- Update chore files
  ([`7fd19a8`](https://github.com/pivoshenko/uv-upsync/commit/7fd19a8ee74f894e59c2937f6dc1a9c20d8bd56b))


## v2.1.0 (2026-01-29)

### Bug Fixes

- Add compatibility wrapper for HTTPStatusError
  ([`52e568c`](https://github.com/pivoshenko/uv-upsync/commit/52e568c9a8e1de6ea5922bb46fae33ae811c0fe9))

### Build System

- Replace mypy with ty
  ([`2b3f7b4`](https://github.com/pivoshenko/uv-upsync/commit/2b3f7b45e402eada570802757d364e335b536029))


## v2.0.3 (2026-01-10)

### Build System

- Update dev dependencies
  ([`7f47498`](https://github.com/pivoshenko/uv-upsync/commit/7f474982a91b84275d15086e827af48379eef5bc))

- Update dev dependencies
  ([`b95ea2e`](https://github.com/pivoshenko/uv-upsync/commit/b95ea2e883113df0ac8f80c1d26a8cf911c3c305))

- Update dev dependencies
  ([`a43c1b8`](https://github.com/pivoshenko/uv-upsync/commit/a43c1b825c345a265ebec962542a13b7b827547f))

- Update dev dependencies
  ([`85fa4df`](https://github.com/pivoshenko/uv-upsync/commit/85fa4df7c9290057a2e4130b8046edfad14d9a98))

- Update dev dependencies
  ([`8077cdd`](https://github.com/pivoshenko/uv-upsync/commit/8077cdda5dee2278151b0c0d0275989898d4542a))

### Continuous Integration

- Update semantic release action version
  ([`71c4538`](https://github.com/pivoshenko/uv-upsync/commit/71c4538ad98337cce3c5e57f1ee9736057191bac))

- Update version of the Checkout action
  ([`5122582`](https://github.com/pivoshenko/uv-upsync/commit/512258236ade039fe1df2e205fead7ca50a03083))

- Upgrade actions
  ([`4c1e08b`](https://github.com/pivoshenko/uv-upsync/commit/4c1e08b237b7b82acde5499c53283631d9597b56))

### Documentation

- Update license
  ([`ad76913`](https://github.com/pivoshenko/uv-upsync/commit/ad76913c6a0772a775934c6cad7a599e3d7e019e))


## v2.0.2 (2025-11-02)

### Documentation

- Update contribution instructions for testing and formatting commands
  ([`03b2b76`](https://github.com/pivoshenko/uv-upsync/commit/03b2b768f183204e5d579f497a193d77efd88390))


## v2.0.1 (2025-11-02)

### Build System

- Update dev dependencies
  ([`219e2d3`](https://github.com/pivoshenko/uv-upsync/commit/219e2d3629a801d82f49bc712307067b92f04dec))

### Chores

- Update .gitignore
  ([`dd5b926`](https://github.com/pivoshenko/uv-upsync/commit/dd5b92682ecc1e4c278a518cd0c7c56b301b4217))

- Update Commitizen config
  ([`2feeeaf`](https://github.com/pivoshenko/uv-upsync/commit/2feeeaf3da7f4f719cd23a6c78010b7a95a43f84))

### Code Style

- Sort metadata keys
  ([`454315b`](https://github.com/pivoshenko/uv-upsync/commit/454315b21cd068e08f1fe0e5cdfe7daf1475e253))

### Continuous Integration

- Remove force option from semantic release configuration
  ([`ee8399c`](https://github.com/pivoshenko/uv-upsync/commit/ee8399c762a8def4e920519144ff0fa7938d296f))


## v2.0.0 (2025-10-28)

### Build System

- Downgrade Pytest
  ([`9e9e324`](https://github.com/pivoshenko/uv-upsync/commit/9e9e3245aa074559b6243c45fd98cc4b4d07a795))

- Update dev dependencies
  ([`86074b4`](https://github.com/pivoshenko/uv-upsync/commit/86074b4d0bd187b60ab424bad32e066601b2e07a))

- Update dev dependencies
  ([`ce1fd09`](https://github.com/pivoshenko/uv-upsync/commit/ce1fd095b3f9aa6bf92ebf5d2c8345e2c44a779f))

### Continuous Integration

- Remove unused pytest option from configuration
  ([`27e0603`](https://github.com/pivoshenko/uv-upsync/commit/27e060330879d0295e7c951a10e7b527c14f2f00))

- Update codecov action version
  ([`a18066e`](https://github.com/pivoshenko/uv-upsync/commit/a18066e9795e456c77c5436d8aac381c4c60e7cc))

### Documentation

- Update notes
  ([`397e7b1`](https://github.com/pivoshenko/uv-upsync/commit/397e7b14759df8aa3e556123b46d219035216b0b))

### Features

- Add support for updating specific dependency groups
  ([`933b9d9`](https://github.com/pivoshenko/uv-upsync/commit/933b9d9ee5b630001b4d067f31eaa29d5c05025a))

- Rename project from uv-plugin-up to uv-upsync and update related assets
  ([`c1902fd`](https://github.com/pivoshenko/uv-upsync/commit/c1902fd8b3a43fa61705be21741d1fd3634dae91))


## v1.1.2 (2025-10-11)

### Documentation

- Update notes
  ([`238ee5c`](https://github.com/pivoshenko/uv-upsync/commit/238ee5c765910c4c9dc272bee926420032b94c99))


## v1.1.1 (2025-10-11)

### Chores

- Update pyproject.toml with metadata, keywords, and classifiers
  ([`4be0660`](https://github.com/pivoshenko/uv-upsync/commit/4be0660bc99e09b52e4f46429a2da4943462bc03))

### Documentation

- Remove TOC
  ([`d0fd385`](https://github.com/pivoshenko/uv-upsync/commit/d0fd385e550701a35b2ac155cf83c99f5476957c))

- Update notes
  ([`ca6fd27`](https://github.com/pivoshenko/uv-upsync/commit/ca6fd27e384bad381750d0c98f5e6fd628d81732))


## v1.1.0 (2025-10-11)

### Bug Fixes

- Enhance help text for package exclusion option to indicate multiple values are allowed
  ([`0c0459f`](https://github.com/pivoshenko/uv-upsync/commit/0c0459f7b988434e83ee52c322b626df584b9fca))

### Chores

- Update Coverage config
  ([`ff07da6`](https://github.com/pivoshenko/uv-upsync/commit/ff07da604b7ab71f2d1e34e27500b98b5d390723))


## v1.0.0 (2025-10-11)

- Initial Release
