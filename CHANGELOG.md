# CHANGELOG


## v0.33.0 (2024-10-22)

### Documentation

* docs: updated README with latest recipes ([`5eda62d`](https://github.com/mbari-org/aipipeline/commit/5eda62d665972ce3e8b2c29576659b2f0733d839))

### Features

* feat: added vss remove e.g. j remove-vss uav --doc \'doc:boat:\*\' ([`06b02d9`](https://github.com/mbari-org/aipipeline/commit/06b02d9905269335d3e533b3065cdab19ff27eea))


## v0.32.0 (2024-10-22)

### Features

* feat: add --min-variance to vss-init ([`c838aae`](https://github.com/mbari-org/aipipeline/commit/c838aae0e939f569fa8ca4ec52d9a3620590a316))


## v0.31.2 (2024-10-22)

### Bug Fixes

* fix(bio): correct vignette logic ([`e18ff74`](https://github.com/mbari-org/aipipeline/commit/e18ff748dee59a4bca9d432d4bb8e2390058757a))


## v0.31.1 (2024-10-22)

### Bug Fixes

* fix(bio): normalize coords ([`b42cec4`](https://github.com/mbari-org/aipipeline/commit/b42cec46371aefe73033c22a1b8dc1420f6615a5))


## v0.31.0 (2024-10-22)

### Features

* feat(bio): add --remove-vignette to remove vignette detections ([`675a501`](https://github.com/mbari-org/aipipeline/commit/675a5015cbfa10395f7229f4ca271158b6c747d7))


## v0.30.0 (2024-10-22)

### Features

* feat(bio): add --skip-vss  to skip over second stage ([`809188f`](https://github.com/mbari-org/aipipeline/commit/809188fad962cb265b254cd2d52631fa7b12e4dd))


## v0.29.0 (2024-10-21)

### Features

* feat(cfe): load media+boxes of mined rare class labels ([`c8b9824`](https://github.com/mbari-org/aipipeline/commit/c8b98245cedbaf8e9827e36a137e64229d8068ff))


## v0.28.2 (2024-10-21)

### Performance Improvements

* perf(bio): add blurriness removal ([`113e7f8`](https://github.com/mbari-org/aipipeline/commit/113e7f8fd3c96469fff593753287fbaebffc1f98))


## v0.28.1 (2024-10-19)

### Performance Improvements

* perf(bio): crop pass to vss, and pass confidence detections less than .9 ([`69c4b99`](https://github.com/mbari-org/aipipeline/commit/69c4b99b5c47471758aa1d587b06ca6569a55624))


## v0.28.0 (2024-10-19)

### Features

* feat(cfe): switch from video to frame mining on images with depth ([`bd5ee13`](https://github.com/mbari-org/aipipeline/commit/bd5ee13e0651d850a4da0ec75416675decd18ec1))


## v0.27.0 (2024-10-18)

### Features

* feat(bio): simple script to delete a particular version ([`39b0788`](https://github.com/mbari-org/aipipeline/commit/39b0788162d92b3c68d283ccad2c0a90f4450701))


## v0.26.1 (2024-10-18)

### Bug Fixes

* fix: continue to load exemplar when missing data as some labels may be missing ([`e3fbdbd`](https://github.com/mbari-org/aipipeline/commit/e3fbdbd7d755f9472d446782454172d074941ee4))


## v0.26.0 (2024-10-18)

### Features

* feat: added load vss only pipeline ([`23c9b78`](https://github.com/mbari-org/aipipeline/commit/23c9b785179feaf8ab232a3bf4b70236780a2a60))

### Performance Improvements

* perf: added vss optimizer ([`e3dc508`](https://github.com/mbari-org/aipipeline/commit/e3dc508030eef2db9af2229b90a73deab7735885))


## v0.25.0 (2024-10-18)

### Bug Fixes

* fix: handle zero cost saliency ([`2d990e4`](https://github.com/mbari-org/aipipeline/commit/2d990e417278de6a2438992cd8a687ce0d8eb7c1))

### Features

* feat: remove low saliency matches from downloaded data to support external data integration ([`7cb5440`](https://github.com/mbari-org/aipipeline/commit/7cb544053840d91875b9fcd129848a54605220b2))


## v0.24.1 (2024-10-18)

### Performance Improvements

* perf(bio): set saliency score to 1000 for download ([`b86f118`](https://github.com/mbari-org/aipipeline/commit/b86f1188405f680085c63cc54c992b5a52851f35))


## v0.24.0 (2024-10-18)

### Features

* feat(cfe): add download_isiis_label_metadata.py for Fernanda ([`6ee109c`](https://github.com/mbari-org/aipipeline/commit/6ee109cf668e05ceb8a988816d12ab2d1248bf6a))


## v0.23.0 (2024-10-17)

### Features

* feat: handle alternative image directory for voc crops ([`0777493`](https://github.com/mbari-org/aipipeline/commit/0777493499824e0d622585c1d792108459aebb8e))


## v0.22.0 (2024-10-17)

### Features

* feat: handle alternative image directory downloads and skipping download for VSS initialization ([`4f74e68`](https://github.com/mbari-org/aipipeline/commit/4f74e681adf945c5d60e3bf5135bc5f0a1d33301))


## v0.21.1 (2024-10-17)

### Performance Improvements

* perf(cfe): switch to depth labeled images for data mining ([`9dd60ae`](https://github.com/mbari-org/aipipeline/commit/9dd60ae7f56a47e25816bdb6b17931234a8b64f2))


## v0.21.0 (2024-10-17)

### Features

* feat: added crop pipeline ([`50e09cd`](https://github.com/mbari-org/aipipeline/commit/50e09cd85a5ad8a0311bc9a55f47cc662e84dae7))

* feat(m3): added m3 config ([`84fe3aa`](https://github.com/mbari-org/aipipeline/commit/84fe3aaa4b681fef154079371e2299100c952d26))


## v0.20.0 (2024-10-17)

### Documentation

* docs: minor typo fix ([`d31b650`](https://github.com/mbari-org/aipipeline/commit/d31b650ca9c94bf81c808a4704b99e1f8439bc17))

### Features

* feat(bio): added download for top concepts ([`3f0372b`](https://github.com/mbari-org/aipipeline/commit/3f0372bed6511ce11e4e585e999184bcd95d64e3))


## v0.19.0 (2024-10-17)

### Bug Fixes

* fix: correct search pattern completion ([`c8d236c`](https://github.com/mbari-org/aipipeline/commit/c8d236c76d3a3f3d008a2c66d04dadbe3c3b6976))

### Features

* feat: added support for optional database update with --update to saliency pipeline ([`ec2c78a`](https://github.com/mbari-org/aipipeline/commit/ec2c78a0620ae9ada6346cfddf80fe23b31143bc))


## v0.18.0 (2024-10-16)

### Features

* feat: support search pattern left off of saliency pipeline ([`4bb9685`](https://github.com/mbari-org/aipipeline/commit/4bb96855c01f4f0ab188e58756abae5f55a7978d))

* feat: added download only pipeline ([`3d85098`](https://github.com/mbari-org/aipipeline/commit/3d8509852593d892a536a57a452673820ff253f1))


## v0.17.0 (2024-10-16)

### Features

* feat: added support for updating the saliency attribute for any project with variable block size, std, and rescaling; run with just compute-saliency uav --scale-percent 50 --min-std 2.0 --block-size 39 --voc-search-pattern <path to your voc/*.xml> ([`6bcb0e4`](https://github.com/mbari-org/aipipeline/commit/6bcb0e4d1b7c216c3758adf24eb20ad289e73507))


## v0.16.6 (2024-10-12)

### Bug Fixes

* fix(bio): pass config dict ([`6dcf8fe`](https://github.com/mbari-org/aipipeline/commit/6dcf8fe527eda17f3e49fcef61b47f5b596fcd9c))


## v0.16.5 (2024-10-12)

### Bug Fixes

* fix(bio): correct clean-up ([`7c2684c`](https://github.com/mbari-org/aipipeline/commit/7c2684cdf9e26a4bc4c0808869a232fe3492a60b))

* fix(bio): correct frame number which was lost during perf update ([`0531405`](https://github.com/mbari-org/aipipeline/commit/05314054bacf93631c59fdf2f5024fa51ffb92ba))


## v0.16.4 (2024-10-11)

### Performance Improvements

* perf(bio): clean-up frame grabs and only run on < 200 meters ([`729f337`](https://github.com/mbari-org/aipipeline/commit/729f33755b0523964bb765b9b0389a8de3c65938))


## v0.16.3 (2024-10-11)

### Performance Improvements

* perf(bio): switch to ffmpeg generation of highest quality jpeg ffmpeg for speed-up ([`42c23cc`](https://github.com/mbari-org/aipipeline/commit/42c23cc2a69374cfe2e73fa3c505759cf8c46e9b))


## v0.16.2 (2024-10-07)

### Performance Improvements

* perf(bio):  check depth before starting ([`d9d74eb`](https://github.com/mbari-org/aipipeline/commit/d9d74ebca0d51cdb834b3eef7a2ba8889d41ed81))


## v0.16.1 (2024-10-07)

### Bug Fixes

* fix(bio): minor correction to the endpoint ([`f22beeb`](https://github.com/mbari-org/aipipeline/commit/f22beeb6888757d38c04c10671c1d0cd72ecfaed))


## v0.16.0 (2024-10-07)

### Features

* feat: added saliency computation and updated docs ([`1920227`](https://github.com/mbari-org/aipipeline/commit/1920227f54a4673d49410af05e10e0fefb9d5ebe))


## v0.15.0 (2024-10-07)

### Features

* feat: support pass through of environment variables to docker ([`19de539`](https://github.com/mbari-org/aipipeline/commit/19de5392564838ba3870959321d8121576c5d433))


## v0.14.1 (2024-10-07)

### Bug Fixes

* fix(bio): added missing TATOR_TOKEN ([`21fcd31`](https://github.com/mbari-org/aipipeline/commit/21fcd313c0fce0cce13fbf83d1c0512a29eacc04))


## v0.14.0 (2024-10-07)

### Documentation

* docs(bio): add test recipe for processing single video with two-stage pipeline ([`41ce64f`](https://github.com/mbari-org/aipipeline/commit/41ce64f570d193902a121b82581d4a81139e13b1))

* docs(bio): resolve video to path ([`7d800fc`](https://github.com/mbari-org/aipipeline/commit/7d800fc4ed25f635a7988b0d475d4874b9d63835))

### Features

* feat(bio): added ancillary data, slightly faster video seek and better logging for multiproc ([`28e0772`](https://github.com/mbari-org/aipipeline/commit/28e07720e275501ec160e2e3655ae461a9d4d73f))


## v0.13.1 (2024-10-03)

### Documentation

* docs(bio): updated README with command line changes ([`1aa0b69`](https://github.com/mbari-org/aipipeline/commit/1aa0b69aecc078a1b8b5bfd1fc3644f054aac279))

### Performance Improvements

* perf(bio): more conservative threshold for second stage vss ([`d8be83f`](https://github.com/mbari-org/aipipeline/commit/d8be83fceff21fb0b3dfe290d34772e962a13b6e))


## v0.13.0 (2024-10-03)

### Features

* feat(bio): added expc metadata docker build and test data ([`8d49c73`](https://github.com/mbari-org/aipipeline/commit/8d49c73cbe1bc41d55d490de9e3ea05b101df2f6))


## v0.12.3 (2024-10-03)

### Bug Fixes

* fix(bio): added missing yaml entry and fix typo ([`811b988`](https://github.com/mbari-org/aipipeline/commit/811b9889283e8cf26ec4196a6cbe8d7454f061aa))


## v0.12.2 (2024-10-03)

### Performance Improvements

* perf(uav):  final assigment for UAV version saliency_MBARI/uav-yolov5-30k_VSS ([`5a8b2e8`](https://github.com/mbari-org/aipipeline/commit/5a8b2e8090a2bce6dc651834b466b2b3cdb1fd14))


## v0.12.1 (2024-10-03)

### Performance Improvements

* perf(uav): load all detections in single docker instance ([`8d3c7c3`](https://github.com/mbari-org/aipipeline/commit/8d3c7c35a00a670e5b35ccbd9d67dffe1470591d))


## v0.12.0 (2024-10-03)

### Features

* feat(bio): added vss second stage ([`c5defea`](https://github.com/mbari-org/aipipeline/commit/c5defea579060ee732132019cc0acf9ab928b97f))


## v0.11.0 (2024-10-03)

### Features

* feat(bio): added support to grab data version by name ([`10a5c09`](https://github.com/mbari-org/aipipeline/commit/10a5c09dd4b09d0a2a6868b5273b90d9815e862f))


## v0.10.5 (2024-10-03)

### Bug Fixes

* fix(bio):  fixed refactoring bugs ([`9f85436`](https://github.com/mbari-org/aipipeline/commit/9f854363f0247f375ba46cad109994812b8145d9))


## v0.10.4 (2024-10-03)

### Performance Improvements

* perf(cfe): reduce detections with saliency, min/max area adjustments ([`676a5e9`](https://github.com/mbari-org/aipipeline/commit/676a5e9f7d6c1813aedf23164fe877c628a4129d))


## v0.10.3 (2024-10-01)

### Performance Improvements

* perf(uav): add Kelp,Bird pass through ([`0c152eb`](https://github.com/mbari-org/aipipeline/commit/0c152eb52deeac1e983d670491a94f0e2e68f10d))


## v0.10.2 (2024-10-01)

### Performance Improvements

* perf(uav): more memory efficient multiproc crop ([`eab6f5d`](https://github.com/mbari-org/aipipeline/commit/eab6f5dd9c0abb1df6c15a7e4ada833a5ede7b27))


## v0.10.1 (2024-09-30)

### Performance Improvements

* perf(uav): faster vss with multiproc crop, correct handling of csv output and pipeline conditional ([`4b6f4f1`](https://github.com/mbari-org/aipipeline/commit/4b6f4f1fb9428b08cc2fb4371fefed9351d5764d))


## v0.10.0 (2024-09-30)

### Bug Fixes

* fix: correct best score average ([`2dff7f3`](https://github.com/mbari-org/aipipeline/commit/2dff7f324d19a04251c8d4dae9c2f3328bf839f2))

### Features

* feat: working two-stage vss pipeline detect for UAV ([`d9c288e`](https://github.com/mbari-org/aipipeline/commit/d9c288e154e2950f130eaa1ea9e2fd5a0864ff29))

### Performance Improvements

* perf: reduce min_std to 2.0 to find more elusive detections like batrays ([`45777ff`](https://github.com/mbari-org/aipipeline/commit/45777ff004c363bceb0997f34a1602cc5c5425c9))


## v0.9.1 (2024-09-29)

### Bug Fixes

* fix(cfe): replace depth by name in CFE images ([`d41cba0`](https://github.com/mbari-org/aipipeline/commit/d41cba058e33ac52fd02538fdf54959a593d6baf))


## v0.9.0 (2024-09-29)

### Features

* feat(uav): added vss to predict pipeline ([`ca52762`](https://github.com/mbari-org/aipipeline/commit/ca52762800576ed408523606b091cf5d605ae3bf))


## v0.8.2 (2024-09-24)

### Bug Fixes

* fix: skip over low scoring threshold ([`8bdc7bf`](https://github.com/mbari-org/aipipeline/commit/8bdc7bf8a1dc681d9f32c1f0de88e69852d7a521))

* fix: better handling of missing exemplars ([`0b05c1a`](https://github.com/mbari-org/aipipeline/commit/0b05c1a664b6d70b501485e8bf6bfe8ea7494dba))

### Build System

* build: add extra args to predict vss and correct download crop config ([`4d0864b`](https://github.com/mbari-org/aipipeline/commit/4d0864ba54aab4a0f92ad0f3743a02ee2cd9183d))


## v0.8.1 (2024-09-24)

### Bug Fixes

* fix: correct termination ([`08e0f5e`](https://github.com/mbari-org/aipipeline/commit/08e0f5eb5eae4f089870fb22bee0ec7dd0442825))


## v0.8.0 (2024-09-23)

### Features

* feat: added isiis mine script ([`3105d01`](https://github.com/mbari-org/aipipeline/commit/3105d014a1f62f9e31de99d778ecace98dbf7f92))


## v0.7.4 (2024-09-19)

### Bug Fixes

* fix: correct config for i2map host ([`bd0a2be`](https://github.com/mbari-org/aipipeline/commit/bd0a2beef954c3d24cd9220b471f8c13be845528))

### Performance Improvements

* perf:  exit on error during predict ([`b747deb`](https://github.com/mbari-org/aipipeline/commit/b747debeb6e2d234786d397034094ca950ba03cc))

* perf: skip over sdcat grid creation ([`095761c`](https://github.com/mbari-org/aipipeline/commit/095761c93f809cc39e00ceac191ed67347cb8885))


## v0.7.3 (2024-09-19)

### Bug Fixes

* fix: correct threshold for scoring vss ([`a7cb0db`](https://github.com/mbari-org/aipipeline/commit/a7cb0db12ccd9cf4aa4f7aa4ca94cd024faadade))


## v0.7.2 (2024-09-16)

### Bug Fixes

* fix: correct path for config setup ([`acf25a2`](https://github.com/mbari-org/aipipeline/commit/acf25a23224c1539f2bbd81f0f245d2839905a33))

* fix: pass through model name and skip if no labels for graceful exit ([`ffe5e1c`](https://github.com/mbari-org/aipipeline/commit/ffe5e1c00541c70ba13b38e5292dce23315d2e03))


## v0.7.1 (2024-09-13)

### Bug Fixes

* fix: add metadata fix for UAV images, correct path for sdcat config and updated missions2process.txt ([`fc42612`](https://github.com/mbari-org/aipipeline/commit/fc4261284ca77d1c939b6e3e11dd606dbaf56a0f))


## v0.7.0 (2024-09-11)

### Features

* feat: added support for more config checks and some refactoring ([`300b46f`](https://github.com/mbari-org/aipipeline/commit/300b46f62613d0734a8b2f62f3c49133b22f15fc))

### Performance Improvements

* perf: added support for block size 39 and std of 5.0 for uav ([`6e7fbe6`](https://github.com/mbari-org/aipipeline/commit/6e7fbe699819e2afebc22a9af7a03dbe1c43e592))


## v0.6.0 (2024-09-05)

### Features

* feat: export confused predictions and comments to a csv for further processing ([`9457a3b`](https://github.com/mbari-org/aipipeline/commit/9457a3bf038675a8bd8399b98e63ec1447f01380))


## v0.5.0 (2024-09-05)

### Bug Fixes

* fix: flag missing exemplar file, break after load and other refactoring ([`7acc573`](https://github.com/mbari-org/aipipeline/commit/7acc573aa60333b4409a93e5cbb46de19168dbe7))

### Features

* feat: plot names in centroids of each class ([`8c5dd39`](https://github.com/mbari-org/aipipeline/commit/8c5dd39b7009df173f77235e4be006ca2c9ecb48))

* feat: working download_crop_pipeline.py with updates for voc-cropper:0.4.3 ([`76ee970`](https://github.com/mbari-org/aipipeline/commit/76ee970b3cfb02509d4cabeecf7bb4ddb886c9e9))

* feat: add override for download crop pipeline for various arguments ([`7a307db`](https://github.com/mbari-org/aipipeline/commit/7a307dbdf7a24596161f3ace683a8f042372bf68))

* feat: add console log to vss accuracy, get class names from redis not config, and handle empty predictions ([`cc5a517`](https://github.com/mbari-org/aipipeline/commit/cc5a5179d67ce95a938bad039f087b120b14b5af))

* feat: add more checks for required keys in config ([`4446d1d`](https://github.com/mbari-org/aipipeline/commit/4446d1dab81da79a221c6d0aa59156d8e95b02e7))

### Performance Improvements

* perf: better handling of missing classes and bump low exemplars to 10 ([`f486fdd`](https://github.com/mbari-org/aipipeline/commit/f486fdd3c6461d8427bf7743b38657ee52256a58))

* perf: report correct number augmented labels and change from 1 to 2 batch clusters ([`a990b70`](https://github.com/mbari-org/aipipeline/commit/a990b708324143b0fb73651cb43129d95d5a8b0a))


## v0.4.0 (2024-08-31)

### Bug Fixes

* fix: added the guano for eval ([`c0c9383`](https://github.com/mbari-org/aipipeline/commit/c0c938350c99f77f3cae6622456342ef323fec6e))

* fix: correct redis port for cfe project ([`c4d2e3f`](https://github.com/mbari-org/aipipeline/commit/c4d2e3f26571549e8be0b455753684ce4a028036))

* fix: add augment data clean in case not run before metric ([`a2dcbea`](https://github.com/mbari-org/aipipeline/commit/a2dcbea88838089b03e9f958ef3ee9bc9f02c7a6))

### Features

* feat: add config for bulk i2map ([`8df2e17`](https://github.com/mbari-org/aipipeline/commit/8df2e17b203097e924cc08348d3ed60b98f24687))

* feat: added skip to download and crop pipeline and add remove data defaults - these should be specified by project ([`dc29285`](https://github.com/mbari-org/aipipeline/commit/dc292850487ac7706263f1342edc1f3f529d1ff2))


## v0.3.2 (2024-08-30)

### Bug Fixes

* fix: removed any augmented data for init vss and other minor improvements to plot names ([`2f040d0`](https://github.com/mbari-org/aipipeline/commit/2f040d0fd8ce8ca5625c6b3b3b891b0d3529d9e8))

### Documentation

* docs: adjust size of plots ([`14bf018`](https://github.com/mbari-org/aipipeline/commit/14bf018afc4e027d20912f7634bc1677838ec31e))

* docs: updated with new metric plots and just recipes ([`0807a9e`](https://github.com/mbari-org/aipipeline/commit/0807a9e85ce62e82741efb324dbb62dc53d4e004))

### Unknown

* reduce cluster size for large image classes ([`20ad2c2`](https://github.com/mbari-org/aipipeline/commit/20ad2c2b1e175c0cfb760f849c93ba25762da19d))


## v0.3.1 (2024-08-28)

### Bug Fixes

* fix: correct uav imports after refactoring munged and merged aidata config ([`9a8bf29`](https://github.com/mbari-org/aipipeline/commit/9a8bf29118684a47ab3982cdea2c0f9874eeb5fd))

* fix: added new uav missions and fixed mission parse for loading images ([`940ed36`](https://github.com/mbari-org/aipipeline/commit/940ed3641bc53663622d584005ba320eb750c34a))

* fix: correct config ath ([`1c53abb`](https://github.com/mbari-org/aipipeline/commit/1c53abbfc2e36b7ff04ceb707df93d29d50c55fe))


## v0.3.0 (2024-08-27)

### Features

* feat: added simclr_augmentations like augmentation and other minor formatting changes ([`0d4493d`](https://github.com/mbari-org/aipipeline/commit/0d4493d93fe614ae27f46d6be7dff85c8c63e4e5))


## v0.2.0 (2024-08-27)

### Build System

* build: added missing pip install to install recipe ([`e4bf1d2`](https://github.com/mbari-org/aipipeline/commit/e4bf1d2b9d5544e659dae01adf8529f7c4340feb))

### Features

* feat: added confusion matrix and more cleaning of metrics code ([`d205072`](https://github.com/mbari-org/aipipeline/commit/d2050720ab279b5dfd4d2ed4d462d115b987270e))


## v0.1.2 (2024-08-26)

### Documentation

* docs: minor typo fix ([`9e7a728`](https://github.com/mbari-org/aipipeline/commit/9e7a7284485e379f9c7da27a864400b124371074))

### Performance Improvements

* perf: add retry to crop with 30 second delay ([`193542b`](https://github.com/mbari-org/aipipeline/commit/193542b6b2b6d935f69829bf88b87b58ee6ec366))


## v0.1.1 (2024-08-26)

### Bug Fixes

* fix: added missing files and reduce docker log names to daily ([`1847fee`](https://github.com/mbari-org/aipipeline/commit/1847feeeb56736f79583d80d92b9a6c4f57d06dd))

### Documentation

* docs: added example tsne plot ([`779e9ae`](https://github.com/mbari-org/aipipeline/commit/779e9ae6d515381d86f22075aef92fbec312f3ac))


## v0.1.0 (2024-08-26)

### Features

* feat: initial commit ([`90e809d`](https://github.com/mbari-org/aipipeline/commit/90e809d35d5f7bafa052951def14f95e9e9d1287))
