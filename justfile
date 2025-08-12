#!/usr/bin/env just --justfile

# copy the default .env file
## Source the .env file and support an alternative name
set dotenv-load := true
set dotenv-filename := x'${ENV_FILE:-.env}'

# Global settings
set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

_default:
  @just --list --unsorted

import 'justfiles/common.just'
import 'justfiles/uav.just'
import 'justfiles/bio.just'
import 'justfiles/vss.just'
import 'justfiles/cfe.just'
import 'justfiles/ptvr.just'
import 'justfiles/i2map.just'
