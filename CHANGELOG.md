# CHANGELOG



## v0.86.0 (2025-08-22)

### Feature

* feat: read base configuration YAML from shared docs server https://docs.mbari.org/internal/ai/projects/config/, make labels optional, and remove unused planktivore configuration files ([`2cb8659`](https://github.com/mbari-org/aipipeline/commit/2cb8659f7d0565636108322396eb74f709576490))


## v0.85.1 (2025-08-14)

### Performance

* perf: bump vits default batch size to 512 and hdbscan batch size to 50000 in cluster_pipeline.py ([`9aca611`](https://github.com/mbari-org/aipipeline/commit/9aca611f0f8ac10510de35ea2e069ccf061890af))

### Unknown

* perf(vss); process by listing subdir which is faster for large image collections ([`b55fe0c`](https://github.com/mbari-org/aipipeline/commit/b55fe0cc35fcd241fb8a2f2c55ef8f85b9b8f771))


## v0.85.0 (2025-08-13)

### Build

* build: replace python-semantic-release/python-semantic-release@master with python-semantic-release ([`af9ab3e`](https://github.com/mbari-org/aipipeline/commit/af9ab3ec1ef2dd6d8ab958e85178e264c860b723))

### Feature

* feat: add support for VSS background and print totals after processing ([`fe4e774`](https://github.com/mbari-org/aipipeline/commit/fe4e774f79ffb86bfe5245029299aa9f7d01a425))

* feat(i2map): simple plot of species &lt; 50 for mining ([`e58dc65`](https://github.com/mbari-org/aipipeline/commit/e58dc652fa69f2e0f96297b3ae7f828c630bd57a))


## v0.84.2 (2025-08-08)

### Fix

* fix: add required sdcat ini files ([`5efa404`](https://github.com/mbari-org/aipipeline/commit/5efa404cfdce199c2f49b949ec499f21298bbfbb))

* fix: handle all types of label inputs Path or string and return expected Apache string output ([`aeeeed6`](https://github.com/mbari-org/aipipeline/commit/aeeeed66019c40c9caf3860f19d66ced366e61b5))

* fix: correct message on failed sdcat.ini ([`a3a03d2`](https://github.com/mbari-org/aipipeline/commit/a3a03d2bca1df194265d6daa476dbbc917642654))

### Performance

* perf: add rotations to mbari_augmentations ([`8b302cf`](https://github.com/mbari-org/aipipeline/commit/8b302cf15041737f734999c059f880304be53118))


## v0.84.1 (2025-08-05)

### Performance

* perf(uav): fixed filtered key point variable for SAM model ([`f117244`](https://github.com/mbari-org/aipipeline/commit/f117244357b9da19b202aeacedcfe1d60c5d0c2f))

* perf(cfe): delete version ([`12c951c`](https://github.com/mbari-org/aipipeline/commit/12c951cc4f9a920404fad5d352c18fdfe64c3598))


## v0.84.0 (2025-07-02)

### Feature

* feat(cfe): added cluster sweep plots, recipes and improved loader to load cluster and detections ([`78b6507`](https://github.com/mbari-org/aipipeline/commit/78b65079ec90971d0b04d908036b498cdafbd965))

### Fix

* fix(cfe): clamp boxes before load to normalized range 0-1 ([`7889141`](https://github.com/mbari-org/aipipeline/commit/78891412a16388ea0724c2fb84f4c672fe60d195))

* fix(cfe): missing crop column and df save ([`84a3253`](https://github.com/mbari-org/aipipeline/commit/84a32535a54acf166ee8aafdd5c4d29a0f0d0ef8))


## v0.83.0 (2025-06-25)

### Feature

* feat(cfe): added efficient roi cleaning script to remove blurry, near-duplicates particles. Keeps near-duplicates that are larger. ([`99137a5`](https://github.com/mbari-org/aipipeline/commit/99137a529c44fa2491ff2e5926dc12f5de7cecae))


## v0.82.0 (2025-06-21)

### Feature

* feat: added vss predict save pipeline ([`42742f8`](https://github.com/mbari-org/aipipeline/commit/42742f8f4857e1980fce4e2f90bfc5ccae64c06e))


## v0.81.0 (2025-06-21)

### Feature

* feat(i2map): export all movflags and better keyframe ([`c23c5c9`](https://github.com/mbari-org/aipipeline/commit/c23c5c943dda0684ddafdede704635e7c05f586c))

### Fix

* fix: add missing import ([`45baa8e`](https://github.com/mbari-org/aipipeline/commit/45baa8e74cb3f86cc9d6a8e0cce0769cebfbf83e))

* fix: return string as expected ([`86c06c0`](https://github.com/mbari-org/aipipeline/commit/86c06c05317794451ef77ffb9670e83ef4cd6541))


## v0.80.0 (2025-06-21)

### Feature

* feat(cfe): added hawaii cluster recipes ([`4775d8e`](https://github.com/mbari-org/aipipeline/commit/4775d8eb878be4a5b275ea5567ab265fad2c1e17))


## v0.79.1 (2025-06-18)

### Fix

* fix(cfe): handle bogus image files with no pattern match ([`71e2d6f`](https://github.com/mbari-org/aipipeline/commit/71e2d6f792d425b5add804a9557b2feaa906e382))

* fix(cfe): return correct code on ERROR and remove console log as its redundant ([`cb731e6`](https://github.com/mbari-org/aipipeline/commit/cb731e62da518712dd646c7765465f09da946e90))


## v0.79.0 (2025-06-09)

### Feature

* feat(cfe): working loader for video and sdcat frame to video load ([`a430f92`](https://github.com/mbari-org/aipipeline/commit/a430f925a0246409a501e73ddeaf4da089550145))

* feat(cfe): loader for sdcat data frames to video with depth ([`a0829bf`](https://github.com/mbari-org/aipipeline/commit/a0829bfa64b43516a96e637499b678a750bd6811))


## v0.78.0 (2025-06-04)

### Documentation

* docs: updated datetime stamp ([`46132dc`](https://github.com/mbari-org/aipipeline/commit/46132dce2ee6a497f53a85430bde0bd2bc46ee60))

* docs: updated README.md with latest recipes ([`73b2020`](https://github.com/mbari-org/aipipeline/commit/73b202005bdb5a144a84e678cdcdb712ec9942de))

### Feature

* feat(cfe): added notebook for determining best near_duplicate measure to remove duplicates in Hawaii data ([`ff5b2a2`](https://github.com/mbari-org/aipipeline/commit/ff5b2a25e7c7afae0387b12e7b667e44cf2930e5))

* feat(uav): scripts to update image metadata by mission of globally ([`dbae140`](https://github.com/mbari-org/aipipeline/commit/dbae1402943be4d4a875c72f32bc4539dc6ec930))

* feat(ptvr): delete a particular data by its version ([`ffa4b38`](https://github.com/mbari-org/aipipeline/commit/ffa4b383dbf7301633c56c76f115a28ef8c5ec5f))

* feat(bio): add planktivore velella examples for use downstream in VSS ([`8cce276`](https://github.com/mbari-org/aipipeline/commit/8cce276bf0f610a28c68b78e340657d00ab576ef))


## v0.77.0 (2025-05-26)

### Feature

* feat: support clean from top-level single directory and check for edge cases ([`35e3c46`](https://github.com/mbari-org/aipipeline/commit/35e3c4687229bff6cb0b32bee98cfaac737f896e))

### Fix

* fix: remove white space typo in library.py ([`caea5d6`](https://github.com/mbari-org/aipipeline/commit/caea5d69adc7a2e6efdb53b62267672993a2fa1d))

### Performance

* perf(ptvr): final parameters for second round of clustering ([`66dc84a`](https://github.com/mbari-org/aipipeline/commit/66dc84a368913fe12adf93d6b2964a3439a0ec49))


## v0.76.3 (2025-05-25)

### Build

* build: add mbari-aidata, pytz deps, and removed duplicate requirements ([`5c9fe47`](https://github.com/mbari-org/aipipeline/commit/5c9fe47b59c5747317a4d7c8b019ccc40d05ecdc))

### Performance

* perf(ptvr): updated model with latest best oerforming /mnt/DeepSea-AI/models/Planktivore/mbari-ptvr-vits-b8-20250513 ([`acdced7`](https://github.com/mbari-org/aipipeline/commit/acdced7266ad7261db882b18cb404831dfd5e4ea))


## v0.76.2 (2025-05-23)

### Fix

* fix(cfe): recipe for video load aligned with new cfedeploy project ([`5aa4805`](https://github.com/mbari-org/aipipeline/commit/5aa4805deec8783ad04b15effee0389a8b1b295c))


## v0.76.1 (2025-05-23)

### Fix

* fix(cfe): fixed loader pipeline, some file renaming for clarity and add platform to element format for flexibility in future loads ([`b09d3ec`](https://github.com/mbari-org/aipipeline/commit/b09d3ece175c7df961225573926068b3d9484534))


## v0.76.0 (2025-05-14)

### Feature

* feat(bio+i2map): more adjustments to detection params, refactoring redis load to pass video_reference_uuid and uri in same queue,  removed confidence factor in soft BIoU ([`1231103`](https://github.com/mbari-org/aipipeline/commit/123110359f0b9b34c38522cbe664befb90493e4b))


## v0.75.0 (2025-05-12)

### Feature

* feat(bio+i2map): add options for --remove-blurry --save-cotrack-video, support cpu tracking and lower min default score for detection and IOU to remove intersecting detections for midwater ([`35368ca`](https://github.com/mbari-org/aipipeline/commit/35368caee856611aa433eb099b4d15c561df3698))

### Fix

* fix: correct args for multicrop ([`bd54c88`](https://github.com/mbari-org/aipipeline/commit/bd54c885ed13790214615570e82d43e732cb04fd))


## v0.74.1 (2025-05-05)

### Fix

* fix(bio): handle missing camera metadata and some renaming for clarity ([`cf737e5`](https://github.com/mbari-org/aipipeline/commit/cf737e534403008ffa0a1cd6cbb82aaca916814a))

### Performance

* perf(bio): clear cuda cache ([`770ba7c`](https://github.com/mbari-org/aipipeline/commit/770ba7cf4e20ac9c697e199b3b47d8afcff82de9))


## v0.74.0 (2025-05-05)

### Feature

* feat(ptvr): example query for mapping version to section ([`b16ddf2`](https://github.com/mbari-org/aipipeline/commit/b16ddf2f0ae1958d9986f4bb780741b26cc9d4bc))


## v0.73.0 (2025-04-26)

### Feature

* feat(cfe): support video loading into separate project through --tator-project 902111-CFE-Deployments override and better naming of docker image based on media ([`2e86a56`](https://github.com/mbari-org/aipipeline/commit/2e86a5660e4ea69bf2103ee24d5d29cc16b164a4))

### Fix

* fix: handle bogus video loads gracefully and simplify docker image name for use on older docker engines ([`f0759dc`](https://github.com/mbari-org/aipipeline/commit/f0759dcf11f7a245844446e6c974db7894b51941))


## v0.72.1 (2025-04-26)

### Fix

* fix: correct plugin module name for latest mbari-aidata pip module ([`1fa5ae9`](https://github.com/mbari-org/aipipeline/commit/1fa5ae90e2f19a4b8376a69bf16b07892f2b10bb))


## v0.72.0 (2025-04-26)

### Feature

* feat(cfe): added scuba as platform ([`4bb425d`](https://github.com/mbari-org/aipipeline/commit/4bb425d9eaf980eb929954dbfc3730031fbdb8fc))


## v0.71.0 (2025-04-26)

### Feature

* feat(cfe): added hawaii video load support ([`8cd839b`](https://github.com/mbari-org/aipipeline/commit/8cd839b3a49e94b1a95b08d6af4773196c39d911))


## v0.70.0 (2025-04-25)

### Feature

* feat: export bad images to .txt for downstream processing in same directory as crops ([`ac331dd`](https://github.com/mbari-org/aipipeline/commit/ac331dd2f8f06bca6613cec1bfe41ae91e9aec99))

### Fix

* fix(bio+i2map): handle file handle failures gracefully in batch via try catch ([`d720848`](https://github.com/mbari-org/aipipeline/commit/d7208480b0ff978b69b3613e6cb7857f00d43f0a))

* fix(bio+i2map): default to h24 as encoder library ([`9f39036`](https://github.com/mbari-org/aipipeline/commit/9f39036e05af26797f3dc7435f9c4f5c9274642b))


## v0.69.2 (2025-04-25)

### Fix

* fix(bio+i2map): correct stride ([`144d503`](https://github.com/mbari-org/aipipeline/commit/144d503e1bba134091553ecadf9aa1e8a4e7fc6b))

### Performance

* perf(bio+i2map): adjust number of parallel videos to 6 and improved detection sensitivity for midwater ([`7955d36`](https://github.com/mbari-org/aipipeline/commit/7955d36e1e16424f4e96589961da7a29d3406573))

* perf(bio+i2map): adjust from 1 to 1% edge threshold ([`a0b1fdc`](https://github.com/mbari-org/aipipeline/commit/a0b1fdcb28e265950c190dc7f5440f562fd2319e))

* perf(bio+i2map): adjust from 1 to 1% edge threshold ([`82cfe4c`](https://github.com/mbari-org/aipipeline/commit/82cfe4cbbfb157ecff14762a307c221c407273a1))


## v0.69.1 (2025-04-24)

### Performance

* perf(bio+i2map): significant speed-up in video processing with faster video read and beam parallel processing; also some minor reorg of files for clarity and updates to README_AWS.md ([`cb7834a`](https://github.com/mbari-org/aipipeline/commit/cb7834a297f2585797e1cc2bfe2c90488ea755b8))

* perf: make docker name creation unique per each run to avoid collisions, e.g. downloading data for same project two ways ([`af6f0c3`](https://github.com/mbari-org/aipipeline/commit/af6f0c3dfe99bc676086b8affd3cd610a1ea9f7a))


## v0.69.0 (2025-04-21)

### Feature

* feat: added --gen-multicrop as optional in download-crop since useful for training data but not for clustering pipelines ([`c05f076`](https://github.com/mbari-org/aipipeline/commit/c05f07627f41864463beab44db6b4dad7429a09c))


## v0.68.2 (2025-04-21)

### Documentation

* docs: updated justfile docs ([`bd0c2c2`](https://github.com/mbari-org/aipipeline/commit/bd0c2c2f00f9c74aea06f0729639ba552dab69d4))

### Performance

* perf(i2MAP): updated model path that matches config.yml ([`e594303`](https://github.com/mbari-org/aipipeline/commit/e5943036a956e6dff2642cef98ab0d8b77664f57))


## v0.68.1 (2025-04-21)

### Fix

* fix: handle invalid characters in docker image names ([`28db7b3`](https://github.com/mbari-org/aipipeline/commit/28db7b32c162d5e157cc1c5fcef1237c4a181624))

* fix: correct docker tag for mbari/aidata ([`f7dce54`](https://github.com/mbari-org/aipipeline/commit/f7dce54e7d8d0e0e357218d7a3b1af94c2a3b970))


## v0.68.0 (2025-04-21)

### Feature

* feat: add support for more-args to download and some refactoring of recipes to pull out the args ([`4bdeb2b`](https://github.com/mbari-org/aipipeline/commit/4bdeb2b2bae2b78c22aa7c892fd7e7315e2ff2bc))


## v0.67.2 (2025-04-21)

### Fix

* fix: handle first frame cached correctly ([`3575f49`](https://github.com/mbari-org/aipipeline/commit/3575f49d85a167a111580bf6260793cc1334a099))


## v0.67.1 (2025-04-18)

### Fix

* fix: revert munged path and add default for dive even if not yet available ([`e59b070`](https://github.com/mbari-org/aipipeline/commit/e59b070e6b9dc2c9cd60a461652ff5f8ceb91ff1))

* fix(bio): remove default class name for general use for any class ([`df7c93c`](https://github.com/mbari-org/aipipeline/commit/df7c93c701c62c994d8816117bc6348216470193))

### Performance

* perf: faster caching of strided frame ([`004f201`](https://github.com/mbari-org/aipipeline/commit/004f201e6e6058d8213903d57e29bf0f874d7314))

* perf: better caching of metadata, parse file timestamp when possible ([`30b31c2`](https://github.com/mbari-org/aipipeline/commit/30b31c245a8b23b205ced75e64919b6ecbc5af61))


## v0.67.0 (2025-04-14)

### Feature

* feat: added missing requirements for moviepy ([`17128da`](https://github.com/mbari-org/aipipeline/commit/17128da6de8076df29a70e232d406bebbc6a23ad))

* feat(i2map): recipe for processing i2MAP strided video and updated paths to midwater detection models ([`0ebe664`](https://github.com/mbari-org/aipipeline/commit/0ebe664cc9821825f3317853884d0096bb18f7c8))


## v0.66.0 (2025-04-14)

### Feature

* feat: fetch video metadata from moviepy and VAM for best support ([`a948686`](https://github.com/mbari-org/aipipeline/commit/a94868607567c1b55638abb50a6427309c0733f5))

* feat: upgrade all config to https://mantis ([`8d42df7`](https://github.com/mbari-org/aipipeline/commit/8d42df7e299668bf1ecb5727d27fa09f0e134a4f))


## v0.65.0 (2025-04-10)

### Feature

* feat(i2map): transcode .mov to .mp4 for better integration with mantis/tator to generate reports and preview results ([`3109f00`](https://github.com/mbari-org/aipipeline/commit/3109f00144af5182217eab7ec4ead751dfe3fe01))

### Performance

* perf(bio): only capture ancillary data when needed and updated recipe for strided processing ([`5df4ff5`](https://github.com/mbari-org/aipipeline/commit/5df4ff5ecb0a47945f4f3d1566296d478401bf65))


## v0.64.0 (2025-04-03)

### Feature

* feat(bio): load single class with e.g. --class-name &#39;Ctenophora sp. A&#39;; supported with both tracking and no tracking ([`c190319`](https://github.com/mbari-org/aipipeline/commit/c190319aef2e0dea423607e8494c49b95168afa0))


## v0.63.0 (2025-04-03)

### Feature

* feat(bio): added max depth and recipe for running strided inference pipeline ([`7763d1e`](https://github.com/mbari-org/aipipeline/commit/7763d1e4427caea2aa3713b0d058659db6e0ed27))


## v0.62.0 (2025-03-31)

### Feature

* feat(bio): added support for running stride video processing in optimized tracking code for best performance; replaces most run_strided_track.py code capability. To use, add --skip-track and --min-frames 0 ([`8c32abc`](https://github.com/mbari-org/aipipeline/commit/8c32abc81b3b94795323d77b28b314e09824002b))


## v0.61.1 (2025-03-30)

### Performance

* perf(ptvr): final sdcat settings for clustering defaults. ([`b9090a2`](https://github.com/mbari-org/aipipeline/commit/b9090a2ce06114cc16e15700ad6bbf26b8184e9a))


## v0.61.0 (2025-03-30)

### Feature

* feat(bio): added standalone clean pipeline for running cleanvision quickly and recipe for downloading all cteno examples tracked from Haddock dives ([`6a3de45`](https://github.com/mbari-org/aipipeline/commit/6a3de4520540860a13b21c243dd3616efd811e4d))


## v0.60.7 (2025-03-29)

### Fix

* fix(ptvr): updated recipe for loading to replace scratch path as needed for load checking ([`011c997`](https://github.com/mbari-org/aipipeline/commit/011c997c9c022af213cc3395167aadc4c34b606d))

### Performance

* perf(bio): added category reduction json in prep for retraining ViTS model ([`e5ec83d`](https://github.com/mbari-org/aipipeline/commit/e5ec83d6f54d70429b9ae037dda5fc7823054e76))


## v0.60.6 (2025-03-20)

### Performance

* perf(bio): adjusted track valid logic ([`76423c0`](https://github.com/mbari-org/aipipeline/commit/76423c0995db4369378a9ccabd6db517b7a2612d))


## v0.60.5 (2025-03-17)

### Fix

* fix(i2map): updated run-mega-track-i2map-video recipe with latest ([`5877ad9`](https://github.com/mbari-org/aipipeline/commit/5877ad9028a27edab86c826a2767f586c0a4c053))


## v0.60.4 (2025-03-17)

### Fix

* fix(cfe): skip over mix, bad, and detritus and save as RGB ([`1b60452`](https://github.com/mbari-org/aipipeline/commit/1b60452964b4e877bf79ac99c0f5d256f08eb77b))

* fix(cfe): put in directory storage expected for vits training ([`cc9d36c`](https://github.com/mbari-org/aipipeline/commit/cc9d36cf98d38e7528bd64e860a0851af20d4be5))


## v0.60.3 (2025-03-14)

### Performance

* perf(ptvr): multiproc adjust_roi.py for fast processing ([`6b7065e`](https://github.com/mbari-org/aipipeline/commit/6b7065e3fb32c112a6e0a6d289c7c860df016b89))

* perf(cfe): multiproc adjust_roi_ifcb.py for fast processing ([`ec7bb9a`](https://github.com/mbari-org/aipipeline/commit/ec7bb9a42c2b07c60bf0ec42410e02f776e1d881))


## v0.60.2 (2025-03-14)

### Performance

* perf(cfe): added adjust_roi_ifcb.py to resize for optimum square image for training ([`90789c3`](https://github.com/mbari-org/aipipeline/commit/90789c360452fcc16bcb0d3ae76c65953b278223))


## v0.60.1 (2025-03-13)

### Performance

* perf(bio): add soft BiOU and reduce IOU from 0.5 to 0.25 to reduce duplicate tracks ([`1f0df4d`](https://github.com/mbari-org/aipipeline/commit/1f0df4d93e7ac4af0360631b5d493f41202c629f))


## v0.60.0 (2025-03-13)

### Documentation

* docs: typo fix and update recipe table ([`c6e5f3f`](https://github.com/mbari-org/aipipeline/commit/c6e5f3f89452e6ff6f4cdddc68595715a3f72e24))

### Feature

* feat: added label parse for label leaf ([`a57154a`](https://github.com/mbari-org/aipipeline/commit/a57154a64427cf3f771424d236c8669231c6798c))


## v0.59.0 (2025-03-10)

### Feature

* feat(ptvr): added sweep for planktivore ([`aca3442`](https://github.com/mbari-org/aipipeline/commit/aca3442454d4da3e3d009b6d33e039f6117da48b))


## v0.58.0 (2025-03-10)

### Feature

* feat: added support for taxonomy tree per project which can subsequently be used with autocomplete when annotators are labeling. ([`a1f8633`](https://github.com/mbari-org/aipipeline/commit/a1f8633318f06e985f1563e2005d654573234e5a))


## v0.57.1 (2025-02-24)

### Performance

* perf(bio): annotate tracks when valid only and some refactoring for clarity ([`d221d92`](https://github.com/mbari-org/aipipeline/commit/d221d923fd039ba943202576da8dac381f001553))

* perf: remove outer 5% of window for inference where blurry ([`ffde534`](https://github.com/mbari-org/aipipeline/commit/ffde5347aa17381ad348448b21373c827172e6dd))

* perf(ptvr): better settings for planktivore clustering with softcluster branch sdcat ([`e7b2373`](https://github.com/mbari-org/aipipeline/commit/e7b23736755708becfc265565d8cabc7865e800b))


## v0.57.0 (2025-02-21)

### Feature

* feat: add display of complete track to compare to ultralytics or die output ([`f625050`](https://github.com/mbari-org/aipipeline/commit/f6250502d7cf087735f833c7dbaed044c8415293))


## v0.56.0 (2025-02-20)

### Feature

* feat(ptvr): add both high and low res datasets to pad+rescale ([`398eef9`](https://github.com/mbari-org/aipipeline/commit/398eef993e6bd8f53fae920298a8f1b189d9c612))


## v0.55.0 (2025-02-20)

### Documentation

* docs: updated README with current status, roadmap, and update date. ([`3445878`](https://github.com/mbari-org/aipipeline/commit/344587816d11b2c02fb3c71eebf3c47dec0ecd24))

### Feature

* feat(ptvr): utility to create optimized ROIS for clustering ([`e1765c4`](https://github.com/mbari-org/aipipeline/commit/e1765c440123138f0257e602467c55a6a4b2d547))


## v0.54.2 (2025-02-20)

### Fix

* fix: YV8_10 correct models centered box to upper left ([`159c85d`](https://github.com/mbari-org/aipipeline/commit/159c85d7e294522d720aaeaaaf6b601007481337))


## v0.54.1 (2025-02-20)

### Fix

* fix: fix frame index on YV8 or 10 models output ([`11a712b`](https://github.com/mbari-org/aipipeline/commit/11a712b5254b867d2900871db66e1be0b10fe5c5))

### Unknown

* bio(chore): default to YV8_10 models if not specified ([`336dc66`](https://github.com/mbari-org/aipipeline/commit/336dc6618177253018a2c1cfa00cacd0ba3d5ae7))


## v0.54.0 (2025-02-19)

### Documentation

* docs(bio): updated readme to video process ([`512937c`](https://github.com/mbari-org/aipipeline/commit/512937c9d9ef6897d247daceefa1a4897b3ed712))

### Feature

* feat(i2map): add override of model, batch size, version, allowed classes ([`a2f49d6`](https://github.com/mbari-org/aipipeline/commit/a2f49d60e8ccd6855855ee659899e45a1406234b))

### Fix

* fix: correct filtering of low confidence detections and GPU device num ([`871d4ec`](https://github.com/mbari-org/aipipeline/commit/871d4ecd96defed3f287b36c94bc2ca3fbc489ef))

### Performance

* perf(i2map): update with latest best performing model and generic download and remove cleanvision dark filter which removes too many labels ([`2e787ff`](https://github.com/mbari-org/aipipeline/commit/2e787ff9a2de1f782b3a01126c809516d02b39e9))


## v0.53.1 (2025-02-19)

### Performance

* perf(bio): allow for short tracks with high confidence and mov ([`41f44e9`](https://github.com/mbari-org/aipipeline/commit/41f44e9cce8514d1b494e8d94ba027d65637fe38))


## v0.53.0 (2025-02-18)

### Feature

* feat: allow override of version in load pipeline ([`016e50c`](https://github.com/mbari-org/aipipeline/commit/016e50c4877baa0b87e4d6981b45e31e4a29c2a1))

### Fix

* fix(bio): correct no load execution, callback arguments, and moved video creation to a callback which is cleaner ([`3c8a954`](https://github.com/mbari-org/aipipeline/commit/3c8a9541d83590d02d57d33af7e515a5ba5cb0c5))

### Performance

* perf: improved augmentations and skip over empty crops ([`2290380`](https://github.com/mbari-org/aipipeline/commit/229038012576fc39f7303043c66f0e07e362ba04))


## v0.52.2 (2025-02-13)

### Fix

* fix(bio): pad output of video to extend 10 frames beyond last and reset the frame position to zero to fix playback misalignment ([`ba545c8`](https://github.com/mbari-org/aipipeline/commit/ba545c8bde298e9f9a48ab0e29263a9ede21f3b7))


## v0.52.1 (2025-02-13)

### Documentation

* docs(bio): updated README with up-to-date example of arguments ([`d74a8d4`](https://github.com/mbari-org/aipipeline/commit/d74a8d448d0bfb43947c1fd17fa9b6bea20e1dc6))

* docs(bio): updated README with up-to-date example of arguments ([`04d62ba`](https://github.com/mbari-org/aipipeline/commit/04d62ba52ea9cc7b12de70c8ee82d5c5f28b0b12))

### Performance

* perf(bio): working with improved stride performance and added skip load logic to avoid overhead of any database calls for development. ([`48ac07f`](https://github.com/mbari-org/aipipeline/commit/48ac07f9d07ae6919ddc5bc9e7630b3cc1bb5e76))


## v0.52.0 (2025-01-28)

### Feature

* feat: add --use-cleanvision as option as it is not appropriate for all datasets ([`eb97d9a`](https://github.com/mbari-org/aipipeline/commit/eb97d9afe0ce72711565659b2617862f8a9f811e))

### Fix

* fix: working vss init with some refactored library calls ([`3730fcb`](https://github.com/mbari-org/aipipeline/commit/3730fcb7ef8b56c87a482151d9edcb9c1a17b090))


## v0.51.3 (2025-01-22)

### Fix

* fix: handle empty data versions ([`2527f4a`](https://github.com/mbari-org/aipipeline/commit/2527f4ab38b94f0965846b6afc2c8c24af2a0ac1))


## v0.51.2 (2025-01-22)

### Performance

* perf(uav): reduce conf to improve detection ([`36c1c5e`](https://github.com/mbari-org/aipipeline/commit/36c1c5e820cd8fcc2ec954ed22c025949acf4911))


## v0.51.1 (2025-01-22)

### Fix

* fix(uav): handle models hosted locally instead of huggingface ([`43ed3cd`](https://github.com/mbari-org/aipipeline/commit/43ed3cda6dda0c3a4cd2db96ee9bbe23a621a569))


## v0.51.0 (2025-01-22)

### Feature

* feat(uav): SAM based segmentation to fix too large boxes on some localizations ([`69e03f0`](https://github.com/mbari-org/aipipeline/commit/69e03f03c79404f4145798ca21f94ed341d02e1a))


## v0.50.0 (2025-01-22)

### Feature

* feat: handle processing non mission collections for evaluating models ([`5fa21c2`](https://github.com/mbari-org/aipipeline/commit/5fa21c2af1cb0ec726fd1441cb0be7418acacb3e))


## v0.49.2 (2025-01-14)

### Fix

* fix(uav): handle bogus path to detections or clusters and use version defined in config.yml ([`cc4cba0`](https://github.com/mbari-org/aipipeline/commit/cc4cba099735ae73da96c0dbf9dd58b69a04f368))


## v0.49.1 (2025-01-13)

### Performance

* perf(uav): support either gpu/cpu processing and load model from local mount for speedup ([`82da909`](https://github.com/mbari-org/aipipeline/commit/82da90991a04183c25a82872212da14956493d2a))


## v0.49.0 (2025-01-13)

### Feature

* feat(i2map): 200 meter cluster bulk and load pipeline; processes and loads top two scores for further exploration of fish clustering and improved training data ([`140cf77`](https://github.com/mbari-org/aipipeline/commit/140cf77a7f411230199d568dba6d4d53d355bce5))

### Fix

* fix: correct clean  imagesearch ([`321cbe5`](https://github.com/mbari-org/aipipeline/commit/321cbe53002391977a9a79de6edc85d90ac6c393))

### Performance

* perf: set CUDA_VISIBLE_DEVICES to expose two GPUs ([`86b1d21`](https://github.com/mbari-org/aipipeline/commit/86b1d21d9cfd0b5822170d588a7fb3ea5df68eb2))

* perf: enable all GPU in docker execution ([`887f910`](https://github.com/mbari-org/aipipeline/commit/887f910dca1d57f4bc8a5d71415168609c19fbc0))


## v0.48.4 (2025-01-10)

### Performance

* perf(i2map): sdcat switch to 8 block model and skip blurry ([`76c5b33`](https://github.com/mbari-org/aipipeline/commit/76c5b3335ff48029984bc678d2c72189abb1cb81))


## v0.48.3 (2025-01-10)

### Performance

* perf(i2map): sdcat switch to 8 block model and skip blurry ([`fa95645`](https://github.com/mbari-org/aipipeline/commit/fa9564564e326843cd4389115cec71ee67d24933))


## v0.48.2 (2025-01-08)

### Performance

* perf: remove 180 rotation in augmentation; this is handled in training now ([`507bacd`](https://github.com/mbari-org/aipipeline/commit/507bacd75e4b163bcddd49997955dfd14c5a00b7))


## v0.48.1 (2025-01-01)

### Performance

* perf(uav): switch to 8 block size model /mnt/DeepSea-AI/models/UAV/mbari-uav-vit-b-8-20241231 ([`490a345`](https://github.com/mbari-org/aipipeline/commit/490a34503163ba305e995d70c1434c95ef3ae89f))


## v0.48.0 (2024-12-31)

### Feature

* feat: generates csv of stats to share with team;combine stats.json in nested directories of multiple versions ([`50931d2`](https://github.com/mbari-org/aipipeline/commit/50931d2b9afa483c7eef1bb37a59bcf7dccd9b40))

* feat(uav): filter results by min score before loading ([`950ea3d`](https://github.com/mbari-org/aipipeline/commit/950ea3d91775eb409780f02a89be6eee8c43d756))

* feat: support --version override in download_crop_pipeline.py ([`a16c3ee`](https://github.com/mbari-org/aipipeline/commit/a16c3eedd84cbdcd91a14e86671939bed8d577d5))

### Fix

* fix(i2map): download filtered results by vars-labelbot and group ([`11a97bc`](https://github.com/mbari-org/aipipeline/commit/11a97bc7ba2ab86dbee1eee7f6da3cdb1ad78575))

### Performance

* perf(i2map): remove dark images ([`9a7c299`](https://github.com/mbari-org/aipipeline/commit/9a7c299972feaa0a250bff13d7075488f5b24290))


## v0.47.2 (2024-12-30)

### Documentation

* docs: updated with latest justfile ([`bf649c4`](https://github.com/mbari-org/aipipeline/commit/bf649c42068ef4a51c3f5bc094cdedb326ec52cc))

### Performance

* perf(uav): switch to latest mbari-uav-vit-b-16-20241230 model ([`948ba99`](https://github.com/mbari-org/aipipeline/commit/948ba995ed47007c110959c9b032e1204ff58889))


## v0.47.1 (2024-12-30)

### Fix

* fix: clean only versioned dir not parent ([`5b830e1`](https://github.com/mbari-org/aipipeline/commit/5b830e1f3448dff40e34859e41133ec454a09954))

* fix: add stats generation after download in download_crop_pipeline.py ([`86237d3`](https://github.com/mbari-org/aipipeline/commit/86237d31a537838505bb8c337500c10b4e93a45b))

* fix: remove voc crop and replace with download in download_crop_pipeline.py ([`016d515`](https://github.com/mbari-org/aipipeline/commit/016d515a758ca93a3cdab4cd999530b8cecd48e5))

* fix(bio): bound boxes before redis load ([`fcf3678`](https://github.com/mbari-org/aipipeline/commit/fcf3678189247156605a2e6cb25ec0e0975ba2d1))

### Performance

* perf(uav): remove near duplicates to reduce training time ([`302479d`](https://github.com/mbari-org/aipipeline/commit/302479d2f7428f8417392a2258ce4db533c03906))


## v0.47.0 (2024-12-23)

### Feature

* feat: added cleanvision to all projects ([`ca24a03`](https://github.com/mbari-org/aipipeline/commit/ca24a03f984a50ccf5dd32eabf122d294e4317fd))


## v0.46.1 (2024-12-22)

### Performance

* perf: add crop resize from aidata to download crop pipeline ([`188044e`](https://github.com/mbari-org/aipipeline/commit/188044e04e061d7d402cdc91415bc78a2d5bd9fe))


## v0.46.0 (2024-12-21)

### Feature

* feat(cfe): RachelCarson/2023/07 ISIIS video load ([`ccdf54e`](https://github.com/mbari-org/aipipeline/commit/ccdf54ea024c0fb565ce2da73f771d0e1bf71b36))


## v0.45.1 (2024-12-20)

### Fix

* fix(cfe): correct platform parse based on directory naming convention ([`5221134`](https://github.com/mbari-org/aipipeline/commit/5221134ac3fc54539813fb5a0c472f3be6c49471))


## v0.45.0 (2024-12-20)

### Feature

* feat(cfe): added common args for cfe and added missing  mission_name ([`5aff45d`](https://github.com/mbari-org/aipipeline/commit/5aff45d022721c67ebb00572ddb7cf3dc2fb52e3))


## v0.44.0 (2024-12-20)

### Feature

* feat(cfe): video loading pipeline initial check-in ([`a7200ab`](https://github.com/mbari-org/aipipeline/commit/a7200ab690aaa2978b37b4e540bb021c0038635f))


## v0.43.5 (2024-12-19)

### Fix

* fix: handle failed video capture and simplify args ([`14dd788`](https://github.com/mbari-org/aipipeline/commit/14dd788a188bb24302faa27aab27f5e11cee1b51))

* fix: switch to frame stride and correct conversion of tracking coordinates ([`485cbfb`](https://github.com/mbari-org/aipipeline/commit/485cbfb282584abd2cee29cc1d543d20c5db4f67))


## v0.43.4 (2024-12-17)

### Build

* build: fix build conflict in apache-beam/transformers/pyyaml ([`01b19df`](https://github.com/mbari-org/aipipeline/commit/01b19df0b6f29bd8d940b61e68355347b9b875e5))

### Performance

* perf(bio): parallel crop ([`764f524`](https://github.com/mbari-org/aipipeline/commit/764f52465e3f878cade6a7119801e31190f89fef))


## v0.43.3 (2024-12-17)

### Performance

* perf: remove short low scoring tracks ([`c8aed2d`](https://github.com/mbari-org/aipipeline/commit/c8aed2de6221d62979820a90af9c098fe39e97a7))


## v0.43.2 (2024-12-17)

### Performance

* perf: move crop to GPU ([`bd11c3e`](https://github.com/mbari-org/aipipeline/commit/bd11c3edb2cac485f76fbae3656c5d88c75b4af2))


## v0.43.1 (2024-12-17)

### Performance

* perf(bio): significant refactor of video processing pipeline into more modular design with callbacks and moved most data to GPU where possible for speed-up. ([`1b3d972`](https://github.com/mbari-org/aipipeline/commit/1b3d972041fe705318cbbab7728e7e281c23dc52))


## v0.43.0 (2024-12-12)

### Documentation

* docs(bio): updated just recipe to include install and processing of single videos and dives ([`6540634`](https://github.com/mbari-org/aipipeline/commit/6540634ed815e20f185c27d812106c9ee70cfb8e))

### Feature

* feat(bio): pass through separate score threshold for det/track ([`2d34434`](https://github.com/mbari-org/aipipeline/commit/2d34434e92aede9f9a833b2fe8daa0aa5657daed))

### Fix

* fix(bio): handle both fractional and non-fractional seconds from metadata query and bump empty frames to 5 ([`4c4dbf0`](https://github.com/mbari-org/aipipeline/commit/4c4dbf0b5625f9026466db47b54a61129beefb65))


## v0.42.0 (2024-12-12)

### Feature

* feat(bio): some refactoring, plus added second label_s/score_s based on gcam which is proving to be informative and remove any detections that are blurry which are not useful for detection/tracking ([`f2799b8`](https://github.com/mbari-org/aipipeline/commit/f2799b88b4ca7fc70c91a59308a06a80d323b00b))


## v0.41.1 (2024-12-06)

### Performance

* perf: added vits models to project where model exists and clean for sdcat pipeline ([`0a16c0a`](https://github.com/mbari-org/aipipeline/commit/0a16c0af1a24581823d0aa456b1ff0629564849b))


## v0.41.0 (2024-11-26)

### Feature

* feat(uav): jelly heat map ([`bebb389`](https://github.com/mbari-org/aipipeline/commit/bebb389e9fd0e7fe7626e623821bd63bbedf1fce))


## v0.40.6 (2024-11-23)

### Fix

* fix(uav): skip over exemplars when loading clustered detections ([`ee81689`](https://github.com/mbari-org/aipipeline/commit/ee81689e9c31a5c49d2c566728138f235467c068))


## v0.40.5 (2024-11-22)

### Performance

* perf(uav): increase min saliency to 300 in detect ([`e622e20`](https://github.com/mbari-org/aipipeline/commit/e622e20546034b497fd0563a3db9ac92149f3337))


## v0.40.4 (2024-11-22)

### Performance

* perf(bio): add vits model to strided video track ([`4c9027a`](https://github.com/mbari-org/aipipeline/commit/4c9027a82cad578fdee30ab1d7cf2c4e3ebefe80))


## v0.40.3 (2024-11-22)

### Performance

* perf(uav): switch to one class detection model and --use-vits in clustering MBARI-org/mbari-uav-vit-b-16 ([`80da5c2`](https://github.com/mbari-org/aipipeline/commit/80da5c2fcb828a51cded25af47c695a2e3f313ac))


## v0.40.2 (2024-11-21)

### Fix

* fix: correct parsing of download args ([`09f0a90`](https://github.com/mbari-org/aipipeline/commit/09f0a90a88bb8f8df52de470cb442db2e0243ee0))


## v0.40.1 (2024-11-21)

### Fix

* fix: support vss load all ([`3d748aa`](https://github.com/mbari-org/aipipeline/commit/3d748aa8d9bdba2f851acc3b1eba96a49288bbdc))


## v0.40.0 (2024-11-19)

### Feature

* feat(uav): bump min_std from 2. to 4. to reduce detections and run vss after cluster for auto label ([`e735f94`](https://github.com/mbari-org/aipipeline/commit/e735f94158385b5b3d0fc980236b2b24327dcef3))

### Performance

* perf: remove is_near_duplicate_issue from clean and add 180 deg augmentation ([`72253e5`](https://github.com/mbari-org/aipipeline/commit/72253e523dbe59cd44c0abda9442676933da78a4))


## v0.39.1 (2024-11-19)

### Documentation

* docs: more cleanining of recipes and updated dep build to include biotrack ([`8f3b2e7`](https://github.com/mbari-org/aipipeline/commit/8f3b2e7e8e12955d7b302dbb499d9ef65c681fac))

### Fix

* fix: correct check for exemplar files with v0.38.2 perf improvement ([`86f585a`](https://github.com/mbari-org/aipipeline/commit/86f585a0ec3c2b6dffdd891caa6bfe97b336cbdd))


## v0.39.0 (2024-11-15)

### Documentation

* docs: updated recipes ([`a0bb70c`](https://github.com/mbari-org/aipipeline/commit/a0bb70ca4a06349aa42ffc1758db4663850dd607))

### Feature

* feat(bio): added two-stage strided track pipeline ([`1a9cc1b`](https://github.com/mbari-org/aipipeline/commit/1a9cc1b87cab28a7dd3d8b30efcc56a6f1791f2b))

### Fix

* fix: add missing dependency ([`c118d35`](https://github.com/mbari-org/aipipeline/commit/c118d35269a9a1eeb268f6fc341a4d1686def297))


## v0.38.2 (2024-11-14)

### Performance

* perf: skip cluster in vss pipeline for &lt; 2000 detections ([`2591116`](https://github.com/mbari-org/aipipeline/commit/2591116f1c687bfb45a4a38f0436b433ae3aded9))


## v0.38.1 (2024-11-12)

### Fix

* fix: add default EXIF fields if missing ([`580643e`](https://github.com/mbari-org/aipipeline/commit/580643e7c51fc44b7c15e841f427a5e74347a989))


## v0.38.0 (2024-11-11)

### Feature

* feat: add originating bounding box to crop for use in downstream processing in EXIF comment field, e.g. UserComment: b&#39;bbox:534,16,817,300&#39; ([`ad49140`](https://github.com/mbari-org/aipipeline/commit/ad4914080e10a44e9f9ea9f04c9934370463eeed))


## v0.37.0 (2024-11-08)

### Feature

* feat: added vss to UAV processing pipeline ([`df81cc1`](https://github.com/mbari-org/aipipeline/commit/df81cc1916de205ac421e9b3dac9b56c6e29bb88))

### Fix

* fix: correct dictionary item for vss project ([`afd99e0`](https://github.com/mbari-org/aipipeline/commit/afd99e031a96cb627b3b5b46ca7e9c2d45f08273))

### Performance

* perf: removed color jitter from aug and remove all issues, dark, clurry, duplicate, near-duplicate and only cluster is &gt; 500 examples for vss ([`7a38228`](https://github.com/mbari-org/aipipeline/commit/7a38228642548239d6456c030062fb8550dc3924))

* perf: mostly some cleaning of args and logging for vss_predict_pipeline.py but also bumped the batch size to 20 for faster prediction ([`84608ad`](https://github.com/mbari-org/aipipeline/commit/84608ad77eb8d81d97db9872e902b8e16b43d42d))


## v0.36.5 (2024-11-07)

### Fix

* fix: correct args to download_crop_pipeline.py ([`c6a4fe7`](https://github.com/mbari-org/aipipeline/commit/c6a4fe742758b087db57a7cb0f3114392a62488e))


## v0.36.4 (2024-11-07)

### Fix

* fix: correct check for parent of bound volumes and pass through args to download_crop_pipeline.py ([`9906488`](https://github.com/mbari-org/aipipeline/commit/9906488ff3776172da6e63b9125d092271c41e5a))


## v0.36.3 (2024-11-04)

### Fix

* fix: pass through additional args in download_pipeline.py ([`ed7ae48`](https://github.com/mbari-org/aipipeline/commit/ed7ae48a9a591f3cd0cabc547e84d2e84900f145))


## v0.36.2 (2024-10-29)

### Fix

* fix(bio): correct max_seconds args ([`03dd84e`](https://github.com/mbari-org/aipipeline/commit/03dd84ef7a40acbec59af0659df0ac2d137c41c5))


## v0.36.1 (2024-10-29)

### Fix

* fix(bio): correct normalization of localization and handle exceptions in vss ([`3349391`](https://github.com/mbari-org/aipipeline/commit/33493910a4f4c8563a709f8e9da20ae1d0e7ba9d))


## v0.36.0 (2024-10-29)

### Build

* build: added co-tracker submodule ([`4bcd71a`](https://github.com/mbari-org/aipipeline/commit/4bcd71a09504e16ef91e1156c09d010925180753))

* build:  added submodule for co-tracker and better formatting for cluster-uav ([`8aaef9b`](https://github.com/mbari-org/aipipeline/commit/8aaef9b0938a2beb735ee1da925d8792e4694970))

### Feature

* feat(bio): added support for --skip-load and --max-seconds to save just localizations ([`c5f6cda`](https://github.com/mbari-org/aipipeline/commit/c5f6cda79d5d9e350945195af69c2074b92b748a))


## v0.35.6 (2024-10-28)

### Performance

* perf(uav): remove any low saliency detections from clustering ([`43b316c`](https://github.com/mbari-org/aipipeline/commit/43b316c51203cb046cc1a10f3aeea125cc8ce354))


## v0.35.5 (2024-10-28)

### Performance

* perf: clean vss images with cleanvision defaults removing all dark and blurry images ([`1ccb994`](https://github.com/mbari-org/aipipeline/commit/1ccb994a63cd150b22e51fc0cce23495c5faa758))


## v0.35.4 (2024-10-25)

### Performance

* perf(uav): exclude unused classes, lower threshold for vss to allow more rare detections, and cluster everything ([`c7d12b6`](https://github.com/mbari-org/aipipeline/commit/c7d12b65afb0f6aefa96d5b5e9c368fdfbda2b63))


## v0.35.3 (2024-10-24)

### Fix

* fix(bio): removed unused args ([`1038aa7`](https://github.com/mbari-org/aipipeline/commit/1038aa7d8167d8089525440447d806318d21ba4f))


## v0.35.2 (2024-10-24)

### Fix

* fix(bio): pass through addtional args ([`3bf1b74`](https://github.com/mbari-org/aipipeline/commit/3bf1b74e40c7cb8ae1e592db67325a678dc61fc5))


## v0.35.1 (2024-10-24)

### Fix

* fix: minor logging correction ([`544f3b7`](https://github.com/mbari-org/aipipeline/commit/544f3b77b9549b962fef060c27ced79ebe2959ab))


## v0.35.0 (2024-10-23)

### Feature

* feat(bio): added --allowed-classes animal with --class-remap &#34;{&#39;animal&#39;: &#39;marine organism&#39;}&#34; ([`1306116`](https://github.com/mbari-org/aipipeline/commit/13061161de26b75b0b569f4bcad90f606af7f963))


## v0.34.1 (2024-10-23)

### Performance

* perf: load all detections if less than 100 total examples ([`7ec6053`](https://github.com/mbari-org/aipipeline/commit/7ec6053ce5f545690f79d4fb060abef28cd111d1))


## v0.34.0 (2024-10-22)

### Feature

* feat(i2map): change group MERGE_CLASSIFY to NMS ([`6fb7265`](https://github.com/mbari-org/aipipeline/commit/6fb72654e32b9b705d4e82efd6d61e10355716c3))

* feat(cfe): delete all media by depth ([`41a60f9`](https://github.com/mbari-org/aipipeline/commit/41a60f9969dcf59b394741293cca8bc7352403d1))

* feat(uav): delete all loc in media ([`6323700`](https://github.com/mbari-org/aipipeline/commit/63237007002aacd2d9d0ad0c8f31b460fd8bc450))


## v0.33.0 (2024-10-22)

### Documentation

* docs: updated README with latest recipes ([`5eda62d`](https://github.com/mbari-org/aipipeline/commit/5eda62d665972ce3e8b2c29576659b2f0733d839))

### Feature

* feat: added vss remove e.g. j remove-vss uav --doc \&#39;doc:boat:\*\&#39; ([`06b02d9`](https://github.com/mbari-org/aipipeline/commit/06b02d9905269335d3e533b3065cdab19ff27eea))


## v0.32.0 (2024-10-22)

### Feature

* feat: add --min-variance to vss-init ([`c838aae`](https://github.com/mbari-org/aipipeline/commit/c838aae0e939f569fa8ca4ec52d9a3620590a316))


## v0.31.2 (2024-10-22)

### Fix

* fix(bio): correct vignette logic ([`e18ff74`](https://github.com/mbari-org/aipipeline/commit/e18ff748dee59a4bca9d432d4bb8e2390058757a))


## v0.31.1 (2024-10-22)

### Fix

* fix(bio): normalize coords ([`b42cec4`](https://github.com/mbari-org/aipipeline/commit/b42cec46371aefe73033c22a1b8dc1420f6615a5))


## v0.31.0 (2024-10-22)

### Feature

* feat(bio): add --remove-vignette to remove vignette detections ([`675a501`](https://github.com/mbari-org/aipipeline/commit/675a5015cbfa10395f7229f4ca271158b6c747d7))


## v0.30.0 (2024-10-22)

### Feature

* feat(bio): add --skip-vss  to skip over second stage ([`809188f`](https://github.com/mbari-org/aipipeline/commit/809188fad962cb265b254cd2d52631fa7b12e4dd))


## v0.29.0 (2024-10-21)

### Feature

* feat(cfe): load media+boxes of mined rare class labels ([`c8b9824`](https://github.com/mbari-org/aipipeline/commit/c8b98245cedbaf8e9827e36a137e64229d8068ff))


## v0.28.2 (2024-10-21)

### Performance

* perf(bio): add blurriness removal ([`113e7f8`](https://github.com/mbari-org/aipipeline/commit/113e7f8fd3c96469fff593753287fbaebffc1f98))


## v0.28.1 (2024-10-19)

### Performance

* perf(bio): crop pass to vss, and pass confidence detections less than .9 ([`69c4b99`](https://github.com/mbari-org/aipipeline/commit/69c4b99b5c47471758aa1d587b06ca6569a55624))


## v0.28.0 (2024-10-19)

### Feature

* feat(cfe): switch from video to frame mining on images with depth ([`bd5ee13`](https://github.com/mbari-org/aipipeline/commit/bd5ee13e0651d850a4da0ec75416675decd18ec1))


## v0.27.0 (2024-10-18)

### Feature

* feat(bio): simple script to delete a particular version ([`39b0788`](https://github.com/mbari-org/aipipeline/commit/39b0788162d92b3c68d283ccad2c0a90f4450701))


## v0.26.1 (2024-10-18)

### Fix

* fix: continue to load exemplar when missing data as some labels may be missing ([`e3fbdbd`](https://github.com/mbari-org/aipipeline/commit/e3fbdbd7d755f9472d446782454172d074941ee4))


## v0.26.0 (2024-10-18)

### Feature

* feat: added load vss only pipeline ([`23c9b78`](https://github.com/mbari-org/aipipeline/commit/23c9b785179feaf8ab232a3bf4b70236780a2a60))

### Performance

* perf: added vss optimizer ([`e3dc508`](https://github.com/mbari-org/aipipeline/commit/e3dc508030eef2db9af2229b90a73deab7735885))


## v0.25.0 (2024-10-18)

### Feature

* feat: remove low saliency matches from downloaded data to support external data integration ([`7cb5440`](https://github.com/mbari-org/aipipeline/commit/7cb544053840d91875b9fcd129848a54605220b2))

### Fix

* fix: handle zero cost saliency ([`2d990e4`](https://github.com/mbari-org/aipipeline/commit/2d990e417278de6a2438992cd8a687ce0d8eb7c1))


## v0.24.1 (2024-10-18)

### Performance

* perf(bio): set saliency score to 1000 for download ([`b86f118`](https://github.com/mbari-org/aipipeline/commit/b86f1188405f680085c63cc54c992b5a52851f35))


## v0.24.0 (2024-10-18)

### Feature

* feat(cfe): add download_isiis_label_metadata.py for Fernanda ([`6ee109c`](https://github.com/mbari-org/aipipeline/commit/6ee109cf668e05ceb8a988816d12ab2d1248bf6a))


## v0.23.0 (2024-10-17)

### Feature

* feat: handle alternative image directory for voc crops ([`0777493`](https://github.com/mbari-org/aipipeline/commit/0777493499824e0d622585c1d792108459aebb8e))


## v0.22.0 (2024-10-17)

### Feature

* feat: handle alternative image directory downloads and skipping download for VSS initialization ([`4f74e68`](https://github.com/mbari-org/aipipeline/commit/4f74e681adf945c5d60e3bf5135bc5f0a1d33301))


## v0.21.1 (2024-10-17)

### Performance

* perf(cfe): switch to depth labeled images for data mining ([`9dd60ae`](https://github.com/mbari-org/aipipeline/commit/9dd60ae7f56a47e25816bdb6b17931234a8b64f2))


## v0.21.0 (2024-10-17)

### Feature

* feat: added crop pipeline ([`50e09cd`](https://github.com/mbari-org/aipipeline/commit/50e09cd85a5ad8a0311bc9a55f47cc662e84dae7))

* feat(m3): added m3 config ([`84fe3aa`](https://github.com/mbari-org/aipipeline/commit/84fe3aaa4b681fef154079371e2299100c952d26))


## v0.20.0 (2024-10-17)

### Documentation

* docs: minor typo fix ([`d31b650`](https://github.com/mbari-org/aipipeline/commit/d31b650ca9c94bf81c808a4704b99e1f8439bc17))

### Feature

* feat(bio): added download for top concepts ([`3f0372b`](https://github.com/mbari-org/aipipeline/commit/3f0372bed6511ce11e4e585e999184bcd95d64e3))


## v0.19.0 (2024-10-17)

### Feature

* feat: added support for optional database update with --update to saliency pipeline ([`ec2c78a`](https://github.com/mbari-org/aipipeline/commit/ec2c78a0620ae9ada6346cfddf80fe23b31143bc))

### Fix

* fix: correct search pattern completion ([`c8d236c`](https://github.com/mbari-org/aipipeline/commit/c8d236c76d3a3f3d008a2c66d04dadbe3c3b6976))


## v0.18.0 (2024-10-16)

### Feature

* feat: support search pattern left off of saliency pipeline ([`4bb9685`](https://github.com/mbari-org/aipipeline/commit/4bb96855c01f4f0ab188e58756abae5f55a7978d))

* feat: added download only pipeline ([`3d85098`](https://github.com/mbari-org/aipipeline/commit/3d8509852593d892a536a57a452673820ff253f1))


## v0.17.0 (2024-10-16)

### Feature

* feat: added support for updating the saliency attribute for any project with variable block size, std, and rescaling; run with just compute-saliency uav --scale-percent 50 --min-std 2.0 --block-size 39 --voc-search-pattern &lt;path to your voc/*.xml&gt; ([`6bcb0e4`](https://github.com/mbari-org/aipipeline/commit/6bcb0e4d1b7c216c3758adf24eb20ad289e73507))


## v0.16.6 (2024-10-12)

### Fix

* fix(bio): pass config dict ([`6dcf8fe`](https://github.com/mbari-org/aipipeline/commit/6dcf8fe527eda17f3e49fcef61b47f5b596fcd9c))


## v0.16.5 (2024-10-12)

### Fix

* fix(bio): correct clean-up ([`7c2684c`](https://github.com/mbari-org/aipipeline/commit/7c2684cdf9e26a4bc4c0808869a232fe3492a60b))

* fix(bio): correct frame number which was lost during perf update ([`0531405`](https://github.com/mbari-org/aipipeline/commit/05314054bacf93631c59fdf2f5024fa51ffb92ba))


## v0.16.4 (2024-10-11)

### Performance

* perf(bio): clean-up frame grabs and only run on &lt; 200 meters ([`729f337`](https://github.com/mbari-org/aipipeline/commit/729f33755b0523964bb765b9b0389a8de3c65938))


## v0.16.3 (2024-10-11)

### Performance

* perf(bio): switch to ffmpeg generation of highest quality jpeg ffmpeg for speed-up ([`42c23cc`](https://github.com/mbari-org/aipipeline/commit/42c23cc2a69374cfe2e73fa3c505759cf8c46e9b))


## v0.16.2 (2024-10-07)

### Performance

* perf(bio):  check depth before starting ([`d9d74eb`](https://github.com/mbari-org/aipipeline/commit/d9d74ebca0d51cdb834b3eef7a2ba8889d41ed81))


## v0.16.1 (2024-10-07)

### Fix

* fix(bio): minor correction to the endpoint ([`f22beeb`](https://github.com/mbari-org/aipipeline/commit/f22beeb6888757d38c04c10671c1d0cd72ecfaed))


## v0.16.0 (2024-10-07)

### Feature

* feat: added saliency computation and updated docs ([`1920227`](https://github.com/mbari-org/aipipeline/commit/1920227f54a4673d49410af05e10e0fefb9d5ebe))


## v0.15.0 (2024-10-07)

### Feature

* feat: support pass through of environment variables to docker ([`19de539`](https://github.com/mbari-org/aipipeline/commit/19de5392564838ba3870959321d8121576c5d433))


## v0.14.1 (2024-10-07)

### Fix

* fix(bio): added missing TATOR_TOKEN ([`21fcd31`](https://github.com/mbari-org/aipipeline/commit/21fcd313c0fce0cce13fbf83d1c0512a29eacc04))


## v0.14.0 (2024-10-07)

### Documentation

* docs(bio): add test recipe for processing single video with two-stage pipeline ([`41ce64f`](https://github.com/mbari-org/aipipeline/commit/41ce64f570d193902a121b82581d4a81139e13b1))

* docs(bio): resolve video to path ([`7d800fc`](https://github.com/mbari-org/aipipeline/commit/7d800fc4ed25f635a7988b0d475d4874b9d63835))

### Feature

* feat(bio): added ancillary data, slightly faster video seek and better logging for multiproc ([`28e0772`](https://github.com/mbari-org/aipipeline/commit/28e07720e275501ec160e2e3655ae461a9d4d73f))


## v0.13.1 (2024-10-03)

### Documentation

* docs(bio): updated README with command line changes ([`1aa0b69`](https://github.com/mbari-org/aipipeline/commit/1aa0b69aecc078a1b8b5bfd1fc3644f054aac279))

### Performance

* perf(bio): more conservative threshold for second stage vss ([`d8be83f`](https://github.com/mbari-org/aipipeline/commit/d8be83fceff21fb0b3dfe290d34772e962a13b6e))


## v0.13.0 (2024-10-03)

### Feature

* feat(bio): added expc metadata docker build and test data ([`8d49c73`](https://github.com/mbari-org/aipipeline/commit/8d49c73cbe1bc41d55d490de9e3ea05b101df2f6))


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
