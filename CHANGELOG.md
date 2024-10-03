# CHANGELOG

## v0.12.3 (2024-10-03)

### Fix

* fix(bio): added missing yaml entry and fix typo ([`811b988`](https://github.com/mbari-org/aipipeline/commit/811b9889283e8cf26ec4196a6cbe8d7454f061aa))

## v0.12.2 (2024-10-03)

### Performance

* perf(uav):  final assigment for UAV version saliency_MBARI/uav-yolov5-30k_VSS ([`5a8b2e8`](https://github.com/mbari-org/aipipeline/commit/5a8b2e8090a2bce6dc651834b466b2b3cdb1fd14))

## v0.12.1 (2024-10-03)

### Performance

* perf(uav): load all detections in single docker instance ([`8d3c7c3`](https://github.com/mbari-org/aipipeline/commit/8d3c7c35a00a670e5b35ccbd9d67dffe1470591d))

## v0.12.0 (2024-10-03)

### Feature

* feat(bio): added vss second stage ([`c5defea`](https://github.com/mbari-org/aipipeline/commit/c5defea579060ee732132019cc0acf9ab928b97f))

## v0.11.0 (2024-10-03)

### Feature

* feat(bio): added support to grab data version by name ([`10a5c09`](https://github.com/mbari-org/aipipeline/commit/10a5c09dd4b09d0a2a6868b5273b90d9815e862f))

## v0.10.5 (2024-10-03)

### Fix

* fix(bio):  fixed refactoring bugs ([`9f85436`](https://github.com/mbari-org/aipipeline/commit/9f854363f0247f375ba46cad109994812b8145d9))

## v0.10.4 (2024-10-03)

### Performance

* perf(cfe): reduce detections with saliency, min/max area adjustments ([`676a5e9`](https://github.com/mbari-org/aipipeline/commit/676a5e9f7d6c1813aedf23164fe877c628a4129d))

## v0.10.3 (2024-10-01)

### Performance

* perf(uav): add Kelp,Bird pass through ([`0c152eb`](https://github.com/mbari-org/aipipeline/commit/0c152eb52deeac1e983d670491a94f0e2e68f10d))

## v0.10.2 (2024-10-01)

### Performance

* perf(uav): more memory efficient multiproc crop ([`eab6f5d`](https://github.com/mbari-org/aipipeline/commit/eab6f5dd9c0abb1df6c15a7e4ada833a5ede7b27))

## v0.10.1 (2024-09-30)

### Performance

* perf(uav): faster vss with multiproc crop, correct handling of csv output and pipeline conditional ([`4b6f4f1`](https://github.com/mbari-org/aipipeline/commit/4b6f4f1fb9428b08cc2fb4371fefed9351d5764d))

## v0.10.0 (2024-09-30)

### Feature

* feat: working two-stage vss pipeline detect for UAV ([`d9c288e`](https://github.com/mbari-org/aipipeline/commit/d9c288e154e2950f130eaa1ea9e2fd5a0864ff29))

### Fix

* fix: correct best score average ([`2dff7f3`](https://github.com/mbari-org/aipipeline/commit/2dff7f324d19a04251c8d4dae9c2f3328bf839f2))

### Performance

* perf: reduce min_std to 2.0 to find more elusive detections like batrays ([`45777ff`](https://github.com/mbari-org/aipipeline/commit/45777ff004c363bceb0997f34a1602cc5c5425c9))

## v0.9.1 (2024-09-29)

### Fix

* fix(cfe): replace depth by name in CFE images ([`d41cba0`](https://github.com/mbari-org/aipipeline/commit/d41cba058e33ac52fd02538fdf54959a593d6baf))

## v0.9.0 (2024-09-29)

### Feature

* feat(uav): added vss to predict pipeline ([`ca52762`](https://github.com/mbari-org/aipipeline/commit/ca52762800576ed408523606b091cf5d605ae3bf))

## v0.8.2 (2024-09-24)

### Build

* build: add extra args to predict vss and correct download crop config ([`4d0864b`](https://github.com/mbari-org/aipipeline/commit/4d0864ba54aab4a0f92ad0f3743a02ee2cd9183d))

### Fix

* fix: skip over low scoring threshold ([`8bdc7bf`](https://github.com/mbari-org/aipipeline/commit/8bdc7bf8a1dc681d9f32c1f0de88e69852d7a521))

* fix: better handling of missing exemplars ([`0b05c1a`](https://github.com/mbari-org/aipipeline/commit/0b05c1a664b6d70b501485e8bf6bfe8ea7494dba))

## v0.8.1 (2024-09-24)

### Fix

* fix: correct termination ([`08e0f5e`](https://github.com/mbari-org/aipipeline/commit/08e0f5eb5eae4f089870fb22bee0ec7dd0442825))

## v0.8.0 (2024-09-23)

### Feature

* feat: added isiis mine script ([`3105d01`](https://github.com/mbari-org/aipipeline/commit/3105d014a1f62f9e31de99d778ecace98dbf7f92))

## v0.7.4 (2024-09-19)

### Fix

* fix: correct config for i2map host ([`bd0a2be`](https://github.com/mbari-org/aipipeline/commit/bd0a2beef954c3d24cd9220b471f8c13be845528))

### Performance

* perf:  exit on error during predict ([`b747deb`](https://github.com/mbari-org/aipipeline/commit/b747debeb6e2d234786d397034094ca950ba03cc))

* perf: skip over sdcat grid creation ([`095761c`](https://github.com/mbari-org/aipipeline/commit/095761c93f809cc39e00ceac191ed67347cb8885))

## v0.7.3 (2024-09-19)

### Fix

* fix: correct threshold for scoring vss ([`a7cb0db`](https://github.com/mbari-org/aipipeline/commit/a7cb0db12ccd9cf4aa4f7aa4ca94cd024faadade))

## v0.7.2 (2024-09-16)

### Fix

* fix: correct path for config setup ([`acf25a2`](https://github.com/mbari-org/aipipeline/commit/acf25a23224c1539f2bbd81f0f245d2839905a33))

* fix: pass through model name and skip if no labels for graceful exit ([`ffe5e1c`](https://github.com/mbari-org/aipipeline/commit/ffe5e1c00541c70ba13b38e5292dce23315d2e03))

## v0.7.1 (2024-09-13)

### Fix

* fix: add metadata fix for UAV images, correct path for sdcat config and updated missions2process.txt ([`fc42612`](https://github.com/mbari-org/aipipeline/commit/fc4261284ca77d1c939b6e3e11dd606dbaf56a0f))

## v0.7.0 (2024-09-11)

### Feature

* feat: added support for more config checks and some refactoring ([`300b46f`](https://github.com/mbari-org/aipipeline/commit/300b46f62613d0734a8b2f62f3c49133b22f15fc))

### Performance

* perf: added support for block size 39 and std of 5.0 for uav ([`6e7fbe6`](https://github.com/mbari-org/aipipeline/commit/6e7fbe699819e2afebc22a9af7a03dbe1c43e592))

## v0.6.0 (2024-09-05)

### Feature

* feat: export confused predictions and comments to a csv for further processing ([`9457a3b`](https://github.com/mbari-org/aipipeline/commit/9457a3bf038675a8bd8399b98e63ec1447f01380))

## v0.5.0 (2024-09-05)

### Feature

* feat: plot names in centroids of each class ([`8c5dd39`](https://github.com/mbari-org/aipipeline/commit/8c5dd39b7009df173f77235e4be006ca2c9ecb48))

* feat: working download_crop_pipeline.py with updates for voc-cropper:0.4.3 ([`76ee970`](https://github.com/mbari-org/aipipeline/commit/76ee970b3cfb02509d4cabeecf7bb4ddb886c9e9))

* feat: add override for download crop pipeline for various arguments ([`7a307db`](https://github.com/mbari-org/aipipeline/commit/7a307dbdf7a24596161f3ace683a8f042372bf68))

* feat: add console log to vss accuracy, get class names from redis not config, and handle empty predictions ([`cc5a517`](https://github.com/mbari-org/aipipeline/commit/cc5a5179d67ce95a938bad039f087b120b14b5af))

* feat: add more checks for required keys in config ([`4446d1d`](https://github.com/mbari-org/aipipeline/commit/4446d1dab81da79a221c6d0aa59156d8e95b02e7))

### Fix

* fix: flag missing exemplar file, break after load and other refactoring ([`7acc573`](https://github.com/mbari-org/aipipeline/commit/7acc573aa60333b4409a93e5cbb46de19168dbe7))

### Performance

* perf: better handling of missing classes and bump low exemplars to 10 ([`f486fdd`](https://github.com/mbari-org/aipipeline/commit/f486fdd3c6461d8427bf7743b38657ee52256a58))

* perf: report correct number augmented labels and change from 1 to 2 batch clusters ([`a990b70`](https://github.com/mbari-org/aipipeline/commit/a990b708324143b0fb73651cb43129d95d5a8b0a))

## v0.4.0 (2024-08-31)

### Feature

* feat: add config for bulk i2map ([`8df2e17`](https://github.com/mbari-org/aipipeline/commit/8df2e17b203097e924cc08348d3ed60b98f24687))

* feat: added skip to download and crop pipeline and add remove data defaults - these should be specified by project ([`dc29285`](https://github.com/mbari-org/aipipeline/commit/dc292850487ac7706263f1342edc1f3f529d1ff2))

### Fix

* fix: added the guano for eval ([`c0c9383`](https://github.com/mbari-org/aipipeline/commit/c0c938350c99f77f3cae6622456342ef323fec6e))

* fix: correct redis port for cfe project ([`c4d2e3f`](https://github.com/mbari-org/aipipeline/commit/c4d2e3f26571549e8be0b455753684ce4a028036))

* fix: add augment data clean in case not run before metric ([`a2dcbea`](https://github.com/mbari-org/aipipeline/commit/a2dcbea88838089b03e9f958ef3ee9bc9f02c7a6))

## v0.3.2 (2024-08-30)

### Documentation

* docs: adjust size of plots ([`14bf018`](https://github.com/mbari-org/aipipeline/commit/14bf018afc4e027d20912f7634bc1677838ec31e))

* docs: updated with new metric plots and just recipes ([`0807a9e`](https://github.com/mbari-org/aipipeline/commit/0807a9e85ce62e82741efb324dbb62dc53d4e004))

### Fix

* fix: removed any augmented data for init vss and other minor improvements to plot names ([`2f040d0`](https://github.com/mbari-org/aipipeline/commit/2f040d0fd8ce8ca5625c6b3b3b891b0d3529d9e8))

### Unknown

* reduce cluster size for large image classes ([`20ad2c2`](https://github.com/mbari-org/aipipeline/commit/20ad2c2b1e175c0cfb760f849c93ba25762da19d))

## v0.3.1 (2024-08-28)

### Fix

* fix: correct uav imports after refactoring munged and merged aidata config ([`9a8bf29`](https://github.com/mbari-org/aipipeline/commit/9a8bf29118684a47ab3982cdea2c0f9874eeb5fd))

* fix: added new uav missions and fixed mission parse for loading images ([`940ed36`](https://github.com/mbari-org/aipipeline/commit/940ed3641bc53663622d584005ba320eb750c34a))

* fix: correct config ath ([`1c53abb`](https://github.com/mbari-org/aipipeline/commit/1c53abbfc2e36b7ff04ceb707df93d29d50c55fe))

## v0.3.0 (2024-08-27)

### Feature

* feat: added simclr_augmentations like augmentation and other minor formatting changes ([`0d4493d`](https://github.com/mbari-org/aipipeline/commit/0d4493d93fe614ae27f46d6be7dff85c8c63e4e5))

## v0.2.0 (2024-08-27)

### Build

* build: added missing pip install to install recipe ([`e4bf1d2`](https://github.com/mbari-org/aipipeline/commit/e4bf1d2b9d5544e659dae01adf8529f7c4340feb))

### Feature

* feat: added confusion matrix and more cleaning of metrics code ([`d205072`](https://github.com/mbari-org/aipipeline/commit/d2050720ab279b5dfd4d2ed4d462d115b987270e))

## v0.1.2 (2024-08-26)

### Documentation

* docs: minor typo fix ([`9e7a728`](https://github.com/mbari-org/aipipeline/commit/9e7a7284485e379f9c7da27a864400b124371074))

### Performance

* perf: add retry to crop with 30 second delay ([`193542b`](https://github.com/mbari-org/aipipeline/commit/193542b6b2b6d935f69829bf88b87b58ee6ec366))

## v0.1.1 (2024-08-26)

### Documentation

* docs: added example tsne plot ([`779e9ae`](https://github.com/mbari-org/aipipeline/commit/779e9ae6d515381d86f22075aef92fbec312f3ac))

### Fix

* fix: added missing files and reduce docker log names to daily ([`1847fee`](https://github.com/mbari-org/aipipeline/commit/1847feeeb56736f79583d80d92b9a6c4f57d06dd))

## v0.1.0 (2024-08-26)

### Feature

* feat: initial commit ([`90e809d`](https://github.com/mbari-org/aipipeline/commit/90e809d35d5f7bafa052951def14f95e9e9d1287))
